# -*- coding: utf-8 -*-
"""gnn3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/13M3ufQH5TYy3OhJUKQf5xk2RczbuHEmF

# Graph Neural Networks Tutorial

#### 1. Pytorch Geometric Framework
- Understanding Message Passing Scheme in Pytorch Geometric.
- Efficient graph data representations and paralleling minibatching graphs.
- Showcase the implementation of **Graph Convolution Networks** (Kipf & Welling, [SEMI-SUPERVISED CLASSIFICATION WITH GRAPH CONVOLUTIONAL NETWORKS](https://arxiv.org/abs/1609.02907), ICLR 2017), and you should implement **GraphSAGE** (Hamilton et al, [Inductive Representation Learning on Large Graphs](https://arxiv.org/abs/1706.02216), NIPS 2017) in the lab based on message passing scheme.

#### 2. Vertex Classification
- Showcase a model developed based on our GCN implementation to do vertex classification on Cora dataset. 
- Develop a model with **your own** GraphSAGE (with mean/sum/max aggregation) implementation on the same dataset to get insights of difference.

#### 3. Graph Classification
- Implement **GINConv** (Xu et al, [HOW POWERFUL ARE GRAPH NEURAL NETWORKS?](https://arxiv.org/abs/1810.00826), ICLR 2019) on graph classification benchmark dataset (IMDB) and compare different aggregation functions (SUM/MEAN/MAX).

## Setting up working environment

For this tutorial you will need to train a large network, therefore we recommend you work with Google Colaboratory, which provides free GPU time. You will need a Google account to do so. Please log in to your account and go to the following page: https://colab.research.google.com. Then upload this notebook.For GPU support, go to "Edit" -> "Notebook Settings", and select "Hardware accelerator" as "GPU".You will need to install pytorch by running the following cell:
"""

!pip install torch torchvision
!pip install torch-scatter torch-sparse torch-geometric

"""## Pytorch Geometric Framework

#### Generic Message Passing Scheme
Generalizing the convolution operator to irregular domains is typically expressed as a *neighborhood aggregation* or *message passing* scheme.
With $\mathbf{x}^{(k-1)}_i \in \mathbb{R}^F$ denoting node features of node $i$ in layer $(k-1)$ and $\mathbf{e}_{i,j} \in \mathbb{R}^D$ denoting (optional) edge features from node $i$ to node $j$, message passing graph neural networks can be described as

$$
  \mathbf{x}_i^{(k)} = \gamma^{(k)} \left( \mathbf{x}_i^{(k-1)}, \square_{j \in \mathcal{N}(i)} \, \phi^{(k)}\left(\mathbf{x}_i^{(k-1)}, \mathbf{x}_j^{(k-1)},\mathbf{e}_{i,j}\right) \right)
$$

where $\square$ denotes a differentiable, permutation invariant function, *e.g.*, sum, mean or max, and $\gamma$ and $\phi$ denote differentiable functions such as MLPs (Multi Layer Perceptrons).

#### Graph data representations in PyG
Given a *sparse* **Graph** $\mathcal{G}=(\mathbf{X}, (\mathbf{I}, \mathbf{E}))$ with **node features** $\mathbf{X} \in \mathbb{R}^{|V| \times F}$, **edge indices $\mathbf{I} \in \{1, \cdots, N\}^{2 \times |\mathcal{E}|}$**, (optional) **edge features** $\mathbf{E} \in \mathbb{R}^{|\mathcal{E} \times D|}$, it is described by an instance of class `torch_geometric.data.Data`, which holds the corresponding attributes.

We show a simple example of an unweighted and directed graph with four nodes and three edges.

<p align="center"><img width="70%" src="figures/graph_data.png"></p>
"""

import torch
from torch_geometric.data import Data

edge_index = torch.tensor([[2, 1, 3],
                           [0, 0, 2]], dtype=torch.long)
x = torch.tensor([[1], [1], [1]], dtype=torch.float)

data = Data(x=x, edge_index=edge_index)
data

"""#### Mini-Batching Graphs
Neural networks are usually trained in a batch-wise fashion. Minibatch graphs can be efficiently dealt with to achieve parallelization over a mini-batch from creating sparse block diagnoal adjacency matrices and concatenating features and target matrices in the node dimension.


<p align="center"><img width="70%" src="figures/mini_batch_graph.png"></p>

#### Abstract Message Passing Scheme in PyG

PyTorch Geometric provides the `torch_geometric.nn.MessagePassing` base class, which helps in creating such kinds of message passing graph neural networks by automatically taking care of message propagation. The implementation is decoupled into **UPDATE**, **AGGREGATION**, **MESSAGE** functions as:
$$
    \mathbf{x}_i^{(k)} = \mathrm{UPDATE} \left( \mathbf{x}_i, , \mathrm{AGGR}_{j \in \mathcal{N}(i)} \, \mathrm{MESSAGE}^{(k)}\left(\mathbf{x}_i^{(k-1)}, \mathbf{x}_j^{(k-1)},\mathbf{e}_{i,j}\right) \right)    
$$

<p align="center"><img width="70%" src="figures/message_passing.png"></p>

#### Implementing the GCN layer (lecture)

The graph convolutional operator introduced by Kipf & Welling (ICLR 2017) is defined as
$$
        \mathbf{X}^{k} = \mathbf{\hat{D}}^{-1/2} \mathbf{\hat{A}}
        \mathbf{\hat{D}}^{-1/2} \mathbf{X}^{k-1} \mathbf{\Theta},
$$
where $\mathbf{\hat{A}} = \mathbf{A} + \mathbf{I}$ denotes the adjacency matrix with inserted self-loops and
$\hat{D}_{ii} = \sum_{j=0} \hat{A}_{ij}$ its diagonal degree matrix. It is equivalent as:
$$
\mathbf{x}_i^{(k)} = \sum_{j \in \mathcal{N}(i) \cup \{ i \}} \frac{1}{\sqrt{\deg(i)} \cdot \sqrt{deg(j)}} \cdot \left( \mathbf{x}_j^{(k-1)}\mathbf{\Theta} \right),
$$

where neighboring node features are first transformed by a weight matrix $\mathbf{\Theta}$, normalized by their degree, and finally summed up.
This formula can be divided into the following steps:

1. Add self-loops to the adjacency matrix.
2. Linearly transform node feature matrix.
3. Normalize node features.
4. Sum up neighboring node features.
5. Return new node embeddings.
"""

import torch
from torch_geometric.nn import MessagePassing
import math

def glorot(tensor):
    if tensor is not None:
        stdv = math.sqrt(6.0 / (tensor.size(-2) + tensor.size(-1)))
        tensor.data.uniform_(-stdv, stdv)


def zeros(tensor):
    if tensor is not None:
        tensor.data.fill_(0)

        
def add_self_loops(edge_index, num_nodes=None):
    loop_index = torch.arange(0, num_nodes, dtype=torch.long,
                              device=edge_index.device)
    loop_index = loop_index.unsqueeze(0).repeat(2, 1)

    edge_index = torch.cat([edge_index, loop_index], dim=1)

    return edge_index


def degree(index, num_nodes=None, dtype=None):
    out = torch.zeros((num_nodes), dtype=dtype, device=index.device)
    return out.scatter_add_(0, index, out.new_ones((index.size(0))))
        

class GCNConv(MessagePassing):
    def __init__(self, in_channels, out_channels):
        super(GCNConv, self).__init__(aggr='add')  # "Add" aggregation.
        self.lin = torch.nn.Linear(in_channels, out_channels)
        
        self.reset_parameters()
        
    def reset_parameters(self):
        glorot(self.lin.weight)
        zeros(self.lin.bias)

    def forward(self, x, edge_index):
        # x has shape [N, in_channels]
        # edge_index has shape [2, E]
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################
        # Step 1: Add self-loops to the adjacency matrix.
        
        edge_index = add_self_loops(edge_index, num_nodes=x.size(0))

        # Step 2: Linearly transform node feature matrix.
        x = self.lin(x)

        # Step 3-5: Start propagating messages.

        return self.propagate(edge_index, x=x)
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################                




    def message(self, x_j, edge_index, size):
        # x_j has shape [E, out_channels]

        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        # Step 3: Normalize node features.
        row, col = edge_index
        deg = degree(row, size[0], dtype=x_j.dtype)
        deg_inv_sqrt = deg.pow(-0.5)
        deg_inv_sqrt[deg_inv_sqrt == float('inf')] = 0
        norm = deg_inv_sqrt[row] * deg_inv_sqrt[col]

        return norm.view(-1, 1) * x_j        
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################              
        


    def update(self, aggr_out):
        # aggr_out has shape [N, out_channels]

        # Step 5: Return new node embeddings.
        return aggr_out

"""#### Implementing GraphSAGE (lab)

The algorithm of GraphSAGE (*Inductive Representation Learning on Large Graphs (NIPS 2017)*) embedding generation is described as:

<p align="center"><img width="70%" src="graphsage.png"></p>

You are required to implement this algortihm with **MEAN/SUM/MAX** AGGREGATE.
"""

import torch
import torch.nn.functional as F
from torch.nn import Parameter
from torch_geometric.nn.conv import MessagePassing

def uniform(size, tensor):
    bound = 1.0 / math.sqrt(size)
    if tensor is not None:
        tensor.data.uniform_(-bound, bound)


class SAGEConv(MessagePassing):
    def __init__(self, in_channels, out_channels, aggr):
        super(SAGEConv, self).__init__(aggr=aggr)

        self.in_channels = in_channels
        self.out_channels = out_channels

        self.weight = Parameter(torch.Tensor(2 * in_channels, out_channels))
        
        self.reset_parameters()

    def reset_parameters(self):
        uniform(self.weight.size(0), self.weight)

    def forward(self, x, edge_index):
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        return self.propagate(edge_index, x=x)        
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################                    



    def message(self, x_j, edge_weight):
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        return x_j        
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################                    
        


    def update(self, aggr_out, x):
        
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        aggr_out = torch.cat([x, aggr_out], dim=-1)
        aggr_out = torch.matmul(aggr_out, self.weight)
        aggr_out = F.normalize(aggr_out, p=2, dim=-1)

        return aggr_out        
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################

"""## Vertex Classification"""

import os
import os.path as osp
import torch
import torch.nn.functional as F
from torch_geometric.datasets import Planetoid
import torch_geometric.transforms as T

path = osp.join(os.getcwd(), 'data', 'Cora')
dataset = Planetoid(path, 'Cora')

import time

from torch import tensor
from torch.optim import Adam

def run(dataset, model, runs, epochs, lr, weight_decay, early_stopping):

    val_losses, accs, durations = [], [], []
    for _ in range(runs):
        data = dataset[0]
        data = data.to(device)

        model.to(device).reset_parameters()
        optimizer = Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        t_start = time.perf_counter()

        best_val_loss = float('inf')
        test_acc = 0
        val_loss_history = []

        for epoch in range(1, epochs + 1):
            train(model, optimizer, data)
            eval_info = evaluate(model, data)
            eval_info['epoch'] = epoch

            if eval_info['val_loss'] < best_val_loss:
                best_val_loss = eval_info['val_loss']
                test_acc = eval_info['test_acc']

            val_loss_history.append(eval_info['val_loss'])
            if early_stopping > 0 and epoch > epochs // 2:
                tmp = tensor(val_loss_history[-(early_stopping + 1):-1])
                if eval_info['val_loss'] > tmp.mean().item():
                    break

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        t_end = time.perf_counter()

        val_losses.append(best_val_loss)
        accs.append(test_acc)
        durations.append(t_end - t_start)

    loss, acc, duration = tensor(val_losses), tensor(accs), tensor(durations)

    print('Val Loss: {:.4f}, Test Accuracy: {:.3f} ± {:.3f}, Duration: {:.3f}'.
          format(loss.mean().item(),
                 acc.mean().item(),
                 acc.std().item(),
                 duration.mean().item()))


def train(model, optimizer, data):
    model.train()
    optimizer.zero_grad()
    out = model(data)
    loss = F.nll_loss(out[data.train_mask], data.y[data.train_mask])
    loss.backward()
    optimizer.step()


def evaluate(model, data):
    model.eval()

    with torch.no_grad():
        logits = model(data)

    outs = {}
    for key in ['train', 'val', 'test']:
        mask = data['{}_mask'.format(key)]
        loss = F.nll_loss(logits[mask], data.y[mask]).item()
        pred = logits[mask].max(1)[1]
        acc = pred.eq(data.y[mask]).sum().item() / mask.sum().item()

        outs['{}_loss'.format(key)] = loss
        outs['{}_acc'.format(key)] = acc

    return outs

"""#### Build the model with GCN on vertex classification (lecture)"""

runs = 10
epochs = 200
lr = 0.01
weight_decay = 0.0005
early_stopping = 10
hidden = 16
dropout = 0.5
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class Net(torch.nn.Module):
    def __init__(self, dataset):
        super(Net, self).__init__()
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        self.conv1 = GCNConv(dataset.num_features, hidden)
        self.conv2 = GCNConv(hidden, dataset.num_classes)
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################                    


    def reset_parameters(self):
        self.conv1.reset_parameters()
        self.conv2.reset_parameters()

    def forward(self, data):
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        x, edge_index = data.x, data.edge_index
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)        
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################                    

    
run(dataset, Net(dataset), runs, epochs, lr, weight_decay,
    early_stopping)

"""#### Build models with GraphSAGE on vertex classification (lab)"""

## define your own model

class SAGENet(torch.nn.Module):
    def __init__(self, dataset, aggr='mean'):
        super(SAGENet, self).__init__()
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        self.conv1 = SAGEConv(dataset.num_features, hidden, aggr=aggr)
        self.conv2 = SAGEConv(hidden, dataset.num_classes, aggr=aggr)        
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################                    
        
        self.reset_parameters()
        

    def reset_parameters(self):
        self.conv1.reset_parameters()
        self.conv2.reset_parameters()

    def forward(self, data):
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        x, edge_index = data.x, data.edge_index
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################                    
        

    
aggrs = ['mean', 'add', 'max']    

for aggr in aggrs:
    print('GraphSAGE-{}'.format(aggr))
    run(dataset, SAGENet(dataset, aggr), runs, epochs, lr, weight_decay,
        early_stopping)

"""## Graph Classification

While Graph Convolutional Networks (GCN) and GraphSAGE show extraordinary performance on transductive learning and inductive learning problems resepectively, then cannot learn to distinguish certain simple graph structures. **Graph Isomorphism Network (GIN)** is the state-of-the-art graph neural networks, which is provably the most expressive among the class of GNNs and is as powerful as the Weisfeiler-Lehman graph isomorphism test. 

(Theorem 3, How powerful are graph neural networks?) *Let $\mathcal{A} : \mathcal{G} → \mathbb{R}^d$ be a GNN. With a sufficient number of GNN layers, A maps any graphs $G_1$ and $G_2$ that the Weisfeiler-Lehman test of isomorphism decides as non-isomorphic, to different embeddings if the following conditions hold:*

- a) *$\mathcal{A}$ aggregates and updates node features iteratively with*
$$
    h{_v}^{(k)} = \phi \left( h_v^{(k-1)}, f(\{ h_u^{(k-1)}: u\in\mathcal{N}(v) \}) \right)
$$
*where the functions $f$, which operates on multisets, and $\phi$ are injective.*
- b) *$\mathcal{A}$'s graph-level readout, which operates on the multiset ofnode features $\{ h_v^{(k)} \}$ , is injective.*

**Graph Isomorphism Network (GIN)**, that provably satisfies the conditions in Theorem 3, is defined as:
$$
\mathbf{x}^{\prime}_i = h_{\mathbf{\Theta}} \left( (1 + \epsilon) \cdot
        \mathbf{x}_i + \mathrm{AGGR}_{j \in \mathcal{N}(i)} \mathbf{x}_j \right)
$$
$h_{\mathbf{\Theta}}$ denotes a neural network, *.i.e.* a MLP, and AGGR explicitly denotes SUM because of **higher expressive power (than MEAN/MAX)**.

You should implement **GIN-0/GIn-$\epsilon$** with **SUM/MEAN/MAX Aggregation functions** and use **MEAN Readout function** in the end of the network to obtain **graph-level representations**.

<p align="center"><img width="80%" src="figures/aggr.png"></p>
"""

from torch_geometric.datasets import TUDataset
from torch_geometric.utils import degree
import torch_geometric.transforms as T


class NormalizedDegree(object):
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def __call__(self, data):
        deg = degree(data.edge_index[0], dtype=torch.float)
        deg = (deg - self.mean) / self.std
        data.x = deg.view(-1, 1)
        return data


def get_dataset(name, cleaned=False):
    path = osp.join(os.getcwd(), 'data', name)
    dataset = TUDataset(path, name, cleaned=cleaned)
    dataset.data.edge_attr = None

    if dataset.data.x is None:
        max_degree = 0
        degs = []
        for data in dataset:
            degs += [degree(data.edge_index[0], dtype=torch.long)]
            max_degree = max(max_degree, degs[-1].max().item())

        if max_degree < 1000:
            dataset.transform = T.OneHotDegree(max_degree)
        else:
            deg = torch.cat(degs, dim=0).to(torch.float)
            mean, std = deg.mean().item(), deg.std().item()
            dataset.transform = NormalizedDegree(mean, std)

    return dataset

def print_dataset(dataset):
    num_nodes = num_edges = 0
    for data in dataset:
        num_nodes += data.num_nodes
        num_edges += data.num_edges

    print('Name', dataset)
    print('Graphs', len(dataset))
    print('Nodes', num_nodes / len(dataset))
    print('Edges', (num_edges // 2) / len(dataset))
    print('Features', dataset.num_features)
    print('Classes', dataset.num_classes)
    print()


for name in ['IMDB-BINARY']:
    print_dataset(get_dataset(name))

import time

import torch
import torch.nn.functional as F
from torch import tensor
from torch.optim import Adam
from sklearn.model_selection import StratifiedKFold
from torch_geometric.data import DataLoader, DenseDataLoader as DenseLoader


def cross_validation_with_val_set(dataset, model, folds, epochs, batch_size,
                                  lr, lr_decay_factor, lr_decay_step_size,
                                  weight_decay, logger=None):

    val_losses, accs, durations = [], [], []
    for fold, (train_idx, test_idx,
               val_idx) in enumerate(zip(*k_fold(dataset, folds))):

        train_dataset = dataset[train_idx]
        test_dataset = dataset[test_idx]
        val_dataset = dataset[val_idx]
        
        train_loader = DataLoader(train_dataset, batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size, shuffle=False)
        test_loader = DataLoader(test_dataset, batch_size, shuffle=False)        

        model.to(device).reset_parameters()
        optimizer = Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        t_start = time.perf_counter()

        for epoch in range(1, epochs + 1):
            train_loss = train(model, optimizer, train_loader)
            val_losses.append(eval_loss(model, val_loader))
            accs.append(eval_acc(model, test_loader))
            eval_info = {
                'fold': fold,
                'epoch': epoch,
                'train_loss': train_loss,
                'val_loss': val_losses[-1],
                'test_acc': accs[-1],
            }

            if logger is not None:
                logger(eval_info)

            if epoch % lr_decay_step_size == 0:
                for param_group in optimizer.param_groups:
                    param_group['lr'] = lr_decay_factor * param_group['lr']

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        t_end = time.perf_counter()
        durations.append(t_end - t_start)

    loss, acc, duration = tensor(val_losses), tensor(accs), tensor(durations)
    loss, acc = loss.view(folds, epochs), acc.view(folds, epochs)
    loss, argmin = loss.min(dim=1)
    acc = acc[torch.arange(folds, dtype=torch.long), argmin]

    loss_mean = loss.mean().item()
    acc_mean = acc.mean().item()
    acc_std = acc.std().item()
    duration_mean = duration.mean().item()
    print('Val Loss: {:.4f}, Test Accuracy: {:.3f} ± {:.3f}, Duration: {:.3f}'.
          format(loss_mean, acc_mean, acc_std, duration_mean))

    return loss_mean, acc_mean, acc_std


def k_fold(dataset, folds):
    skf = StratifiedKFold(folds, shuffle=True, random_state=12345)

    test_indices, train_indices = [], []
    for _, idx in skf.split(torch.zeros(len(dataset)), dataset.data.y):
        test_indices.append(torch.from_numpy(idx))

    val_indices = [test_indices[i - 1] for i in range(folds)]

    for i in range(folds):
        train_mask = torch.ones(len(dataset), dtype=torch.bool)
        train_mask[test_indices[i]] = 0
        train_mask[val_indices[i]] = 0
        train_indices.append(train_mask.nonzero().view(-1))

    return train_indices, test_indices, val_indices


def num_graphs(data):
    if data.batch is not None:
        return data.num_graphs
    else:
        return data.x.size(0)


def train(model, optimizer, loader):
    model.train()

    total_loss = 0
    for data in loader:
        optimizer.zero_grad()
        data = data.to(device)
        out = model(data)
        loss = F.nll_loss(out, data.y.view(-1))
        loss.backward()
        total_loss += loss.item() * num_graphs(data)
        optimizer.step()
    return total_loss / len(loader.dataset)


def eval_acc(model, loader):
    model.eval()

    correct = 0
    for data in loader:
        data = data.to(device)
        with torch.no_grad():
            pred = model(data).max(1)[1]
        correct += pred.eq(data.y.view(-1)).sum().item()
    return correct / len(loader.dataset)


def eval_loss(model, loader):
    model.eval()

    loss = 0
    for data in loader:
        data = data.to(device)
        with torch.no_grad():
            out = model(data)
        loss += F.nll_loss(out, data.y.view(-1), reduction='sum').item()
    return loss / len(loader.dataset)

"""#### Implement Graph Isomorphism Network (lab)"""

import torch
import torch.nn.functional as F
from torch.nn import Linear, Sequential, ReLU, BatchNorm1d as BN
from torch_geometric.nn import global_mean_pool, MessagePassing
from torch_geometric.utils import remove_self_loops

def reset(nn):
    def _reset(item):
        if hasattr(item, 'reset_parameters'):
            item.reset_parameters()

    if nn is not None:
        if hasattr(nn, 'children') and len(list(nn.children())) > 0:
            for item in nn.children():
                _reset(item)
        else:
            _reset(nn)


class GINConv(MessagePassing):
    def __init__(self, nn, eps=0, train_eps=False, **kwargs):
        super(GINConv, self).__init__(aggr='add', **kwargs)
        self.nn = nn
        self.initial_eps = eps
        if train_eps:
            self.eps = torch.nn.Parameter(torch.Tensor([eps]))
        else:
            self.register_buffer('eps', torch.Tensor([eps]))
        self.reset_parameters()

    def reset_parameters(self):
        reset(self.nn)
        self.eps.data.fill_(self.initial_eps)

    def forward(self, x, edge_index):
        """"""
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        edge_index, _ = remove_self_loops(edge_index)
        out = self.nn((1 + self.eps) * x + self.propagate(edge_index, x=x))
        return out        
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################            
        


    def message(self, x_j):
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        return x_j        
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################

"""#### Implement models with GIN-0/GIN-$\epsilon$ to perform graph classificaiton on IMDB-binary dataset (lab)"""

class GIN0(torch.nn.Module):
    def __init__(self, dataset, num_layers, hidden):
        super(GIN0, self).__init__()
        self.conv1 = GINConv(Sequential(
            Linear(dataset.num_features, hidden),
            ReLU(),
            Linear(hidden, hidden),
            ReLU(),
            BN(hidden),
        ),
                             train_eps=False)
        self.convs = torch.nn.ModuleList()
        for i in range(num_layers - 1):
            self.convs.append(
                GINConv(Sequential(
                    Linear(hidden, hidden),
                    ReLU(),
                    Linear(hidden, hidden),
                    ReLU(),
                    BN(hidden),
                ),
                        train_eps=False))
        self.lin1 = Linear(hidden, hidden)
        self.lin2 = Linear(hidden, dataset.num_classes)

    def reset_parameters(self):
        self.conv1.reset_parameters()
        for conv in self.convs:
            conv.reset_parameters()
        self.lin1.reset_parameters()
        self.lin2.reset_parameters()

    def forward(self, data):
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        x, edge_index, batch = data.x, data.edge_index, data.batch
        x = self.conv1(x, edge_index)
        for conv in self.convs:
            x = conv(x, edge_index)
        x = global_mean_pool(x, batch)
        x = F.relu(self.lin1(x))
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.lin2(x)
        return F.log_softmax(x, dim=-1)
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################                    
        



class GIN(torch.nn.Module):
    def __init__(self, dataset, num_layers, hidden):
        super(GIN, self).__init__()
        self.conv1 = GINConv(Sequential(
            Linear(dataset.num_features, hidden),
            ReLU(),
            Linear(hidden, hidden),
            ReLU(),
            BN(hidden),
        ),
                             train_eps=True)
        self.convs = torch.nn.ModuleList()
        for i in range(num_layers - 1):
            self.convs.append(
                GINConv(Sequential(
                    Linear(hidden, hidden),
                    ReLU(),
                    Linear(hidden, hidden),
                    ReLU(),
                    BN(hidden),
                ),
                        train_eps=True))
        self.lin1 = Linear(hidden, hidden)
        self.lin2 = Linear(hidden, dataset.num_classes)

    def reset_parameters(self):
        self.conv1.reset_parameters()
        for conv in self.convs:
            conv.reset_parameters()
        self.lin1.reset_parameters()
        self.lin2.reset_parameters()

    def forward(self, data):
        
        ########################################################################
        #      START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)             #
        ########################################################################

        x, edge_index, batch = data.x, data.edge_index, data.batch
        x = self.conv1(x, edge_index)
        for conv in self.convs:
            x = conv(x, edge_index)
        x = global_mean_pool(x, batch)
        x = F.relu(self.lin1(x))
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.lin2(x)
        return F.log_softmax(x, dim=-1)
        
        
        ########################################################################
        #                             END OF YOUR CODE                         #
        ########################################################################

from itertools import product

epochs = 100
batch_size = 128
lr = 0.01
lr_decay_factor = 0.5
lr_decay_step_size = 50

layers = [5]
hiddens = [64]
datasets = ['IMDB-BINARY']
nets = [
    GIN0,
    GIN,
]

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def logger(info):
    fold, epoch = info['fold'] + 1, info['epoch']
    val_loss, test_acc = info['val_loss'], info['test_acc']
    print('{:02d}/{:03d}: Val Loss: {:.4f}, Test Accuracy: {:.3f}'.format(
        fold, epoch, val_loss, test_acc))


results = []
for dataset_name, Net in product(datasets, nets):
    best_result = (float('inf'), 0, 0)  # (loss, acc, std)
    print('-----\n{} - {}'.format(dataset_name, Net.__name__))
    for num_layers, hidden in product(layers, hiddens):
        dataset = get_dataset(dataset_name)
        model = Net(dataset, num_layers, hidden)
        loss, acc, std = cross_validation_with_val_set(
            dataset,
            model,
            folds=10,
            epochs=epochs,
            batch_size=batch_size,
            lr=lr,
            lr_decay_factor=lr_decay_factor,
            lr_decay_step_size=lr_decay_step_size,
            weight_decay=0,
            logger=None,
        )
        if loss < best_result[0]:
            best_result = (loss, acc, std)

    desc = '{:.3f} ± {:.3f}'.format(best_result[1], best_result[2])
    print('Best result - {}'.format(desc))
    results += ['{} - {}: {}'.format(dataset_name, model, desc)]
print('-----\n{}'.format('\n'.join(results)))

from itertools import product

epochs = 100
batch_size = 128
lr = 0.01
lr_decay_factor = 0.5
lr_decay_step_size = 50

layers = [5]
hiddens = [64]
datasets = ['IMDB-BINARY']
nets = [
    GIN0,
    GIN,
]

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def logger(info):
    fold, epoch = info['fold'] + 1, info['epoch']
    val_loss, test_acc = info['val_loss'], info['test_acc']
    print('{:02d}/{:03d}: Val Loss: {:.4f}, Test Accuracy: {:.3f}'.format(
        fold, epoch, val_loss, test_acc))


results = []
for dataset_name, Net in product(datasets, nets):
    best_result = (float('inf'), 0, 0)  # (loss, acc, std)
    print('-----\n{} - {}'.format(dataset_name, Net.__name__))
    for num_layers, hidden in product(layers, hiddens):
        dataset = get_dataset(dataset_name)
        model = Net(dataset, num_layers, hidden)
        loss, acc, std = cross_validation_with_val_set(
            dataset,
            model,
            folds=10,
            epochs=epochs,
            batch_size=batch_size,
            lr=lr,
            lr_decay_factor=lr_decay_factor,
            lr_decay_step_size=lr_decay_step_size,
            weight_decay=0,
            logger=None,
        )
        if loss < best_result[0]:
            best_result = (loss, acc, std)

    desc = '{:.3f} ± {:.3f}'.format(best_result[1], best_result[2])
    print('Best result - {}'.format(desc))
    results += ['{} - {}: {}'.format(dataset_name, model, desc)]
print('-----\n{}'.format('\n'.join(results)))