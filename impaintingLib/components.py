import impaintingLib as imp
import torch
import torchvision
import numpy as np

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

#### Segmentation

classif = imp.loss.getTrainedModel()

def simplifyChannels(x):
    x = np.where(x == 3, 0, x) 
    x = np.where(x == 4, 3, x) 
    x = np.where(x == 5, 3, x) 
    x = np.where(x == 6, 4, x) 
    x = np.where(x == 7, 4, x) 
    x = np.where(x == 8, 5, x) 
    x = np.where(x == 9, 5, x) 
    x = np.where(x == 10 , 6, x) 
    x = np.where(x == 11, 7, x) 
    x = np.where(x == 12, 7, x)  
    x = np.where(x > 12, 0, x)
    return x

def npToTensor(x):
    c,w,h = x.shape
    x = torch.from_numpy(x).to(device)
    x = torch.reshape(x, (c,1,w,h))
    return x.float()

def get_segmentation(x, segmenter=classif, scale_factor=4, simplify=True):
    n,c,w,h = x.shape
    with torch.no_grad():
        if scale_factor > 0 :
            x = torch.nn.functional.interpolate(x, scale_factor=scale_factor)
        x = transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))(x)
        y = classif(x)
        if scale_factor > 0 :
            y = torch.nn.functional.avg_pool2d(y, scale_factor)
            
    y = imp.loss.generate_label_plain(y,w)
    if simplify: 
        y = simplifyChannels(y)
    y =  (y / (np.amax(y)+2)) + 0.1
    y = npToTensor(y)
    return y


#### Keypoints

keypointModel = imp.model.XceptionNet().to(device) 
keypointModel.load_state_dict(torch.load("./modelSave/keypoint.pt"))
keypointModel.eval()

def visualize_batch(images_list, landmarks_list, shape = (1, 8), title = None, save = None):
    n,c,w,h = images_list.shape
    image_dim = w
    fig = plt.figure(figsize = (20, 15))
    grid = ImageGrid(fig, 111, nrows_ncols = shape, axes_pad = 0.08)
    for ax, image, landmarks in zip(grid, images_list, landmarks_list):
        image = (image - image.min())/(image.max() - image.min())
        landmarks = landmarks.view(-1, 2)
        landmarks = (landmarks + 0.5) * image_dim
        landmarks = landmarks.cpu().detach().numpy().tolist()
        landmarks = np.array([(x, y) for (x, y) in landmarks if 0 <= x <= image_dim and 0 <= y <= image_dim])

        ax.imshow(image[0].cpu(), cmap = 'gray')
        ax.scatter(landmarks[:, 0], landmarks[:, 1], s = 10, c = 'dodgerblue')
        ax.axis('off')

    if title:
        print(title)
    if save:
        plt.savefig(save)
    plt.show()
    
def addKeypoints(images_list, landmarks_list, title = None, save = None):
    n,c,w,h = images_list.shape
    image_dim = w
    layers = torch.zeros((n,1, w, h), dtype=images_list.dtype, device=images_list.device)
    for i,(image, landmarks) in enumerate(zip(images_list, landmarks_list)):
        image = (image - image.min())/(image.max() - image.min())
        landmarks = landmarks.view(-1, 2)
        landmarks = (landmarks + 0.5) * image_dim
        landmarks = landmarks.cpu().detach().numpy().tolist()
        landmarks = np.array([(x, y) for (x, y) in landmarks if 0 <= x <= image_dim and 0 <= y <= image_dim])
        landmarks = torch.from_numpy(landmarks).to(device)
        
        layer = torch.empty((1, w, h), dtype=images_list.dtype, device=images_list.device).fill_(0.1)
        for x,y in landmarks:
            x = int(x.item()) - 1
            y = int(y.item()) - 1
            layer[0][y][x] = 1
        layers[i] = layer
    return layers

def getKeypoints(x, model=keypointModel, title = None, save = None):
    x = torchvision.transforms.Grayscale()(x)
    with torch.no_grad():
        keypoints = model(x)
        layers = addKeypoints(x, keypoints, title = title, save = save)
    return layers

def keypointLoss(x,x_hat):
    keypointX = getKeypoints(x)
    keypointX_hat = getKeypoints(x_hat)
    mse = torch.nn.MSELoss()
    loss = mse(keypointX,keypointX_hat)
    if not loss :
        loss = 0
    return loss