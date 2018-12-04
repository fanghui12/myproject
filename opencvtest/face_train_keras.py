# -*- coding: utf-8 -*-

"""

Created on Mon Aug 13 20:53:14 2018



@author: 123

"""

import random

import keras

from sklearn.model_selection import train_test_split

from keras.preprocessing.image import ImageDataGenerator

from keras.models import Sequential

from keras.layers import Dense, Dropout, Activation, Flatten, Conv2D, MaxPooling2D

from keras.models import load_model

from keras import backend as K

import os
import numpy as np
import cv2



'''

对数据集的处理，包括：

1、加载数据集

2、将数据集分为训练集、验证集和测试集

3、根据Keras后端张量操作引擎的不同调整数据维度顺序

4、对数据集中的标签进行One-hot编码

5、数据归一化

'''

IMAGE_SIZE = 64  # 指定图像大小


# 按指定图像大小调整尺寸
def resize_image(image, height=IMAGE_SIZE, width=IMAGE_SIZE):
    top, bottom, left, right = (0, 0, 0, 0)

    # 获取图片尺寸
    h, w, _ = image.shape

    # 对于长宽不等的图片，找到最长的一边
    longest_edge = max(h, w)

    # 计算短边需要增加多少像素宽度才能与长边等长(相当于padding，长边的padding为0，短边才会有padding)
    if h < longest_edge:
        dh = longest_edge - h
        top = dh // 2
        bottom = dh - top
    elif w < longest_edge:
        dw = longest_edge - w
        left = dw // 2
        right = dw - left
    else:
        pass  # pass是空语句，是为了保持程序结构的完整性。pass不做任何事情，一般用做占位语句。

    # RGB颜色
    BLACK = [0, 0, 0]
    # 给图片增加padding，使图片长、宽相等
    # top, bottom, left, right分别是各个边界的宽度，cv2.BORDER_CONSTANT是一种border type，表示用相同的颜色填充
    constant = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=BLACK)
    # 调整图像大小并返回图像，目的是减少计算量和内存占用，提升训练速度
    return cv2.resize(constant, (height, width))


# 读取训练数据到内存，这里数据结构是列表
images = []
labels = []


# path_name是当前工作目录，后面会由os.getcwd()获得
def read_path(path_name):
    for dir_item in os.listdir(path_name):  # os.listdir() 方法用于返回指定的文件夹包含的文件或文件夹的名字的列表
        # 从当前工作目录寻找训练集图片的文件夹
        full_path = os.path.abspath(os.path.join(path_name, dir_item))

        if os.path.isdir(full_path):  # 如果是文件夹，继续递归调用，去读取文件夹里的内容
            read_path(full_path)
        else:  # 如果是文件了
            if dir_item.endswith('.jpg'):
                image = cv2.imread(full_path)
                #                print(type(image))
                if image is None:  # 遇到部分数据有点问题，报错'NoneType' object has no attribute 'shape'
                    pass
                else:
                    image = resize_image(image, IMAGE_SIZE, IMAGE_SIZE)

                    images.append(image)
                    labels.append(path_name)  # 这里最终的path_name是递归过后最终包含图片文件的路径
    return images, labels


# 读取训练数据并完成标注
def load_dataset(path_name):
    images, labels = read_path(path_name)
    # 将lsit转换为numpy array
    images = np.array(images,
                      dtype='float')  # 注意这里要将数据类型设为float，否则后面face_train_keras.py里图像归一化的时候会报错，TypeError: No loop matching the specified signature and casting was found for ufunc true_divide

    #    print(images.shape) # (1969, 64, 64, 3)
    # 标注数据，me文件夹下是我，指定为0，其他指定为1，这里的0和1不是logistic regression二分类输出下的0和1，而是softmax下的多分类的类别
    labels = np.array([0 if label.endswith('me') else 1 for label in labels])
    return images, labels


class Dataset:

    # http://www.runoob.com/python3/python3-class.html

    # 很多类都倾向于将对象创建为有初始状态的。

    # 因此类可能会定义一个名为 __init__() 的特殊方法（构造方法），类定义了 __init__() 方法的话，类的实例化操作会自动调用 __init__() 方法。

    # __init__() 方法可以有参数，参数通过 __init__() 传递到类的实例化操作上，比如下面的参数path_name。

    # 类的方法与普通的函数只有一个特别的区别——它们必须有一个额外的第一个参数名称, 按照惯例它的名称是 self。

    # self 代表的是类的实例，代表当前对象的地址，而 self.class 则指向类。

    def __init__(self, path_name):

        # 训练集

        self.train_images = None

        self.train_labels = None

        # 验证集

        #        self.valid_images = None

        #        self.valid_labels = None

        # 测试集

        self.test_images = None

        self.test_labels = None

        # 数据集加载路径

        self.path_name = path_name

        # 当前库采用的维度顺序，包括rows，cols，channels，用于后续卷积神经网络模型中第一层卷积层的input_shape参数

        self.input_shape = None

        # 加载数据集并按照交叉验证的原则划分数据集并进行相关预处理工作

    def load(self, img_rows=IMAGE_SIZE, img_cols=IMAGE_SIZE, img_channels=3, nb_classes=2):

        # 加载数据集到内存

        images, labels = load_dataset(self.path_name)

        # 注意下面数据集的划分是随机的，所以每次运行程序的训练结果会不一样

        #        train_images, valid_images, train_labels, valid_labels = train_test_split(images, labels, test_size = 0.3, random_state = random.randint(0,100))

        #        print(train_labels) # 有0有1，每次运行都不一样

        # When coding, we often use _ as a "throwaway" variable to store values that we won't need to use later. https://stackoverflow.com/questions/5893163/what-is-the-purpose-of-the-single-underscore-variable-in-python

        #        _, test_images, _, test_labels = train_test_split(images, labels, test_size = 0.5, random_state = random.randint(0, 100))

        train_images, test_images, train_labels, test_labels = train_test_split(images, labels, test_size=0.3,
                                                                                random_state=random.randint(0, 100))

        #        print(test_labels) # 确认了每次都不一样

        # tensorflow 作为后端，数据格式约定是channel_last，与这里数据本身的格式相符，如果是channel_first，就要对数据维度顺序进行一下调整

        if K.image_data_format == 'channel_first':

            train_images = train_images.reshape(train_images.shape[0], img_channels, img_rows, img_cols)

            test_images = test_images.reshape(test_images.shape[0], img_channels, img_rows, img_cols)

            self.input_shape = (img_channels, img_rows, img_cols)

        else:

            train_images = train_images.reshape(train_images.shape[0], img_rows, img_cols, img_channels)

            test_images = test_images.reshape(test_images.shape[0], img_rows, img_cols, img_channels)

            self.input_shape = (img_rows, img_cols, img_channels)

        # 输出训练集、验证集和测试集的数量

        print(train_images.shape[0], 'train samples')

        #        print(valid_images.shape[0], 'valid samples')

        print(test_images.shape[0], 'test samples')

        # 后面模型中会使用categorical_crossentropy作为损失函数，这里要对类别标签进行One-hot编码

        train_labels = keras.utils.to_categorical(train_labels, nb_classes)

        #        valid_labels = keras.utils.to_categorical(valid_labels, nb_classes)

        test_labels = keras.utils.to_categorical(test_labels, nb_classes)

        # 像素数据浮点化以便归一化

        # 55             train_images = train_images.astype('float32')

        # 56             valid_images = valid_images.astype('float32')

        # 57             test_images = test_images.astype('float32')

        # 图像归一化，将图像的各像素值归一化到0~1区间，注意python3中除法运算返回值都是float类型，参考https://blog.csdn.net/hehedadaq/article/details/81099446

        train_images /= 255

        #        valid_images /= 255

        test_images /= 255

        self.train_images = train_images

        #        self.valid_images = valid_images

        self.test_images = test_images

        self.train_labels = train_labels

        #        self.valid_labels = valid_labels

        self.test_labels = test_labels


'''

后续思路：

1、建立卷积神经网络模型

2、训练模型并保存

3、载入训练好的模型，并用其建立预测函数

4、最终程序类似于之前的从摄像头视频提取人脸部分，只是在提取人脸后增加了用预测函数判断是否检测到我，如果检测到我就增加文字提示的功能

'''


# 建立卷积神经网络模型

class Model:

    # 初始化构造方法

    def __init__(self):

        self.model = None

    # 建立模型

    def build_model(self, dataset, nb_classes=2):

        self.model = Sequential()

        self.model.add(Conv2D(32, (3, 3), padding='same',
                              input_shape=dataset.input_shape))  # 当使用该层作为模型第一层时，需要提供 input_shape 参数 （整数元组，不包含batch_size）

        self.model.add(Activation('relu'))

        self.model.add(Conv2D(32, (3, 3)))

        self.model.add(Activation('relu'))

        self.model.add(MaxPooling2D(pool_size=(2, 2)))  # strides默认等于pool_size

        self.model.add(Conv2D(64, (3, 3), padding='same'))

        self.model.add(Activation('relu'))

        self.model.add(Conv2D(64, (3, 3)))

        self.model.add(Activation('relu'))

        self.model.add(MaxPooling2D(pool_size=(2, 2)))

        self.model.add(Dropout(0.25))

        self.model.add(Flatten())

        self.model.add(Dense(512))

        self.model.add(Activation('relu'))

        self.model.add(Dropout(0.25))

        self.model.add(Dense(nb_classes))

        self.model.add(Activation('softmax'))

        # 输出模型概况

    #        self.model.summary()

    # 训练模型

    def train(self, dataset, batch_size=64, nb_epoch=15, data_augmentation=True):

        # https://jovianlin.io/cat-crossentropy-vs-sparse-cat-crossentropy/

        # If your targets are one-hot encoded, use categorical_crossentropy, if your targets are integers, use sparse_categorical_crossentropy.

        self.model.compile(loss='categorical_crossentropy',

                           optimizer='ADAM',

                           metrics=['accuracy'])

        if not data_augmentation:

            self.model.fit(dataset.train_images,dataset.train_labels,batch_size=batch_size, epochs=nb_epoch,shuffle=True)

        # 图像预处理

        else:

            # 是否使输入数据去中心化（均值为0），是否使输入数据的每个样本均值为0，是否数据标准化（输入数据除以数据集的标准差），是否将每个样本数据除以自身的标准差，是否对输入数据施以ZCA白化，数据提升时图片随机转动的角度(这里的范围为0～20)，数据提升时图片水平偏移的幅度（单位为图片宽度的占比，0~1之间的浮点数），和rotation一样在0~0.2之间随机取值，同上，只不过这里是垂直，随机水平翻转，不是对所有图片翻转，随机垂直翻转，同上

            # 每个epoch内都对每个样本以以下配置生成一个对应的增强样本，最终生成了1969*(1-0.3)=1378*10=13780个训练样本，因为下面配置的很多参数都是在一定范围内随机取值，因此每个epoch内生成的样本都不一样

            datagen = ImageDataGenerator(rotation_range=20,

                                         width_shift_range=0.2,

                                         height_shift_range=0.2,

                                         horizontal_flip=True)

            # 计算数据增强所需要的统计数据，计算整个训练样本集的数量以用于特征值归一化、ZCA白化等处理

            #            当且仅当 featurewise_center 或 featurewise_std_normalization 或 zca_whitening 设置为 True 时才需要。

            # 利用生成器开始训练模型

            # flow方法输入原始训练数据，生成批量增强数据

            self.model.fit_generator(datagen.flow(dataset.train_images, dataset.train_labels, batch_size=batch_size),nb_epoch)
             # 这里注意keras2里参数名称是epochs而不是nb_epoch，否则会warning，参考https://stackoverflow.com/questions/46314003/keras-2-fit-generator-userwarning-steps-per-epoch-is-not-the-same-as-the-kera


    def evaluate(self, dataset):
        score = self.model.evaluate(dataset.test_images,dataset.test_labels)  # evaluate返回的结果是list，两个元素分别是test loss和test accuracy
        print( "%s: %.3f%%" % (self.model.metrics_names[1], score[1] * 100))  # 注意这里.3f后面的第二个百分号就是百分号，其余两个百分号则是格式化输出浮点数的语法。

    def save_model(self, file_path):
        self.model.save(file_path)

    def load_model(self, file_path):
        self.model = load_model(file_path)

    def face_predict(self, image):
        # 将探测到的人脸reshape为符合输入要求的尺寸
        image = resize_image(image)
        image = image.reshape((1, IMAGE_SIZE, IMAGE_SIZE, 3))
        # 图片浮点化并归一化
        image = image.astype('float32')  # float32	Single precision float: sign bit, 8 bits exponent, 23 bits mantissa
        image /= 255
        result = self.model.predict(image)
        #        print('result:', result)
        #        print(result.shape) # (1,2)
        #        print(type(result)) # <class 'numpy.ndarray'>
        return result.argmax(axis=-1)  # The axis=-1 in numpy corresponds to the last dimension


if __name__ == '__main__':
    dataset = Dataset('./data_me_dark/')
    dataset.load()
    # 训练模型
    model = Model()
    model.build_model(dataset)
    # 测试训练函数的代码
    model.train(dataset)
    model.evaluate(dataset)
    model.save_model('./model/me.face.model.h5')  # 注意这里要在工作目录下先新建model文件夹，否则会报错：Unable to create file，error message = 'No such file or directory'

    # 用训练集里的图片验证，结果是准确的

#    model = Model()

#    model.load_model(file_path = './model/me.face.model.h5')

#    image_test_her = cv2.imread('./dataset/training_data_her/1000.jpg')

#    image_test_me = cv2.imread('./dataset/training_data_me/1.jpg')

#    test_result = model.face_predict(image_test_her)

#    print(test_result)