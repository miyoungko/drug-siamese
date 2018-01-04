import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import collections
import math
import sys

from torch.autograd import Variable


class DrugModel(nn.Module):
    def __init__(self, input_dim, output_dim, lstm_dim, lstm_layer, 
            learning_rate):

        super(DrugModel, self).__init__()

        # Save model configs
        self.input_dim = input_dim
        self.lstm_dim = lstm_dim
        self.lstm_layer = lstm_layer

        # Baseline LSTM
        self.lstm = nn.LSTM(input_dim, lstm_dim, batch_first=True)

        # Get params and register optimizer
        info, params = self.get_model_params()
        self.optimizer = optim.RMSprop(params, lr=learning_rate,
                alpha=0.95, momentum=0.9, eps=1e-10)
        # self.optimizer = optim.Adam(params, lr=learning_rate)
        self.criterion = nn.MSELoss()
        print(info)

    def init_rnn_h(self, batch_size):
        return Variable(torch.zeros(
            self.lstm_layer*1, batch_size, self.lstm_dim)).cuda()

    # Set Siamese network as basic LSTM
    def siamese_network(self, inputs):
        init_lstm_h = self.init_lstm_h(inputs(0))
        lstm_out, _ = self.s_rnn(inputs, init_lstm_h)
        print(lstm_out.size())
        sys.exit()
        return lstm_out
    
    # Calculate similarity score of vec1 and vec2
    def distance_layer(self, vec1, vec2, distance='cosine'):
        if distance == 'cosine':
            similarity = F.cosine_similarity(
                    vec1 + 1e-16, vec2 + 1e-16, dim=-1)
        elif distance == 'l1':
            similarity = torch.abs(vec1 - vec2)
        elif distance == 'l2':
            similarity = torch.abs((vec1 - vec2) ** 2)
        return similarity

    def forward(self, key1, key2):
        embed1 = self.siamese_network(key1) 
        embed2 = self.siamese_network(key2)
        similarity = self.distance_layer(key1, key2)

        return similarity
    
    def get_loss(self, outputs, targets):
        loss = self.criterion(outputs, targets)
        return loss

    def get_model_params(self):
        params = []
        total_size = 0
        def multiply_iter(p_list):
            out = 1
            for p in p_list:
                out *= p
            return out

        for p in self.parameters():
            if p.requires_grad:
                params.append(p)
                total_size += multiply_iter(p.size())
                # print(p.size())
        return '{}\nparam size: {:,}\n'.format(self, total_size), params

    def save_checkpoint(self, state, checkpoint_dir, filename):
        filename = checkpoint_dir + filename
        print('\t=> save checkpoint %s' % filename)
        torch.save(state, filename)

    def load_checkpoint(self, checkpoint_dir, filename):
        filename = checkpoint_dir + filename
        print('\t=> load checkpoint %s' % filename)
        checkpoint = torch.load(filename)

        self.load_state_dict(checkpoint['state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])

