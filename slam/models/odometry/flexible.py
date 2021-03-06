import tensorflow as tf
import keras.backend as K
from keras.layers import Flatten, Lambda, Reshape, Activation, multiply

from slam.models.layers import (activ,
                                chunk,
                                concat,
                                conv2d,
                                gated_conv2d,
                                dense,
                                construct_outputs,
                                transform_inputs,
                                add_grid)

from slam.utils import mlflow_logging


def construct_encoder(inputs,
                      kernel_sizes=[7, 5, 3, 3, 3, 3],
                      strides=[2, 1, 4, 1, 2, 1],
                      dilation_rates=None,
                      activation='relu',
                      kernel_initializer='glorot_normal',
                      use_gated_convolutions=False,
                      use_batch_norm=False):

    conv = gated_conv2d if use_gated_convolutions else conv2d

    layers = len(strides)
    if dilation_rates is None:
        dilation_rates = [1] * layers

    assert layers == len(dilation_rates) and layers == len(kernel_sizes)

    x = inputs
    for i in range(layers):
        x = conv(x,
                 64,
                 kernel_size=kernel_sizes[i],
                 strides=strides[i],
                 dilation_rate=dilation_rates[i],
                 padding='same',
                 batch_norm=use_batch_norm and i == 0,
                 activation=activation,
                 kernel_initializer=kernel_initializer)

    flatten = Flatten()(x)
    return flatten


@mlflow_logging(ignore=('inputs',), prefix='model.', name='Flexible')
def construct_flexible_model(inputs,
                             kernel_sizes=[7, 5, 3, 3, 3, 3],
                             strides=[2, 1, 4, 1 ,2, 1],
                             dilation_rates=None,
                             output_size=500,
                             regularization=0,
                             activation='relu',
                             kernel_initializer='glorot_normal',
                             use_gated_convolutions=False,
                             use_batch_norm=False,
                             split=False,
                             transform=None,
                             agnostic=True,
                             channel_wise=False,
                             concat_scale_to_fc=False,
                             multiply_outputs_by_scale=False,
                             confidence_mode=None):

    inputs, scale = transform_inputs(inputs,
                                     transform=transform,
                                     agnostic=agnostic,
                                     channel_wise=channel_wise)

    features = construct_encoder(inputs,
                                 kernel_sizes=kernel_sizes,
                                 strides=strides,
                                 dilation_rates=dilation_rates,
                                 activation=activation,
                                 kernel_initializer=kernel_initializer,
                                 use_gated_convolutions=use_gated_convolutions,
                                 use_batch_norm=use_batch_norm)

    if concat_scale_to_fc:
        fc_rotation = features
        fc_translation = features

        for i in range(2):
            fc_rotation = concat([fc_rotation, scale])
            fc_translation = concat([fc_translation, scale])

            fc_rotation = dense(fc_rotation,
                                output_size=output_size,
                                layers_num=1,
                                regularization=regularization,
                                activation=activation,
                                kernel_initializer=kernel_initializer)

            fc_translation = dense(fc_translation,
                                   output_size=output_size,
                                   layers_num=1,
                                   regularization=regularization,
                                   activation=activation,
                                   kernel_initializer=kernel_initializer)
    else:
        fc_rotation = dense(features,
                            output_size=output_size,
                            layers_num=2,
                            regularization=regularization,
                            activation=activation,
                            kernel_initializer=kernel_initializer,
                            name='rotation')
        fc_translation = dense(features,
                               output_size=output_size,
                               layers_num=2,
                               regularization=regularization,
                               activation=activation,
                               kernel_initializer=kernel_initializer,
                               name='translation')

    if split:
        fc = chunk(fc_rotation, n=3) + chunk(fc_translation, n=3)
    else:
        fc = [fc_rotation] * 3 + [fc_translation] * 3

    outputs = construct_outputs(fc,
                                regularization=regularization,
                                scale=scale if multiply_outputs_by_scale else None,
                                confidence_mode=confidence_mode)
    return outputs
