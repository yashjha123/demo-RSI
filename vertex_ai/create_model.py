from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dropout, Flatten, Dense, Conv2D, MaxPooling2D
import tensorflow as tf

model = None
image_height = 224
image_width = 224
channels = 3


def load_model():
    # load the pre-trained Keras model (here we are using a model
    # pre-trained on ImageNet and provided by Keras, but you can
    # substitute in your own networks just as easily)
    #####Define the CNN architecture
    # Create structure of Convolutional Neural Network
    model = Sequential()

    model.add(Conv2D(16, kernel_size=(3, 3),
                     activation='relu',
                     input_shape=(image_height, image_width, channels)))
    #model.add(BatchNormalization())#
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(32, (3, 3), activation='relu'))
    #model.add(BatchNormalization())#
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    #model.add(BatchNormalization())#
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(128, (3, 3), activation='relu'))
    #model.add(BatchNormalization())#
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(256, (3, 3), activation='relu'))
    #model.add(BatchNormalization())#
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.5))
    model.add(Flatten())
    model.add(Dense(1000, activation='relu'))
    #model.add(BatchNormalization())#
    model.add(Dropout(0.5))
    model.add(Dense(1000, activation='relu'))
    #model.add(BatchNormalization())#
    model.add(Dropout(0.5))
    model.add(Dense(4, activation='softmax'))

    model.load_weights('4_retrain_baseline_update_train9.h5')
    # model = tf.keras.models.load_model('./keras_model.h5')
    return model

def preprocess(img_bytes):
    img = tf.image.decode_jpeg(img_bytes, channels=channels)
    img = tf.image.convert_image_dtype(img, tf.float32)
    # return tf.image.resize(img, [image_height, image_width])
    return img

@tf.function(input_signature=[tf.TensorSpec([None,], dtype=tf.string),tf.TensorSpec([None,], dtype=tf.string)])
def predict_bytes(img_bytes,key):
    input_images = tf.map_fn(
        preprocess,
        img_bytes,
        fn_output_signature=tf.float32
    )
    batch_pred = model(input_images) # same as model.predict()
    # top_prob = tf.math.reduce_max(batch_pred, axis=[1])
    # pred_label_index = tf.math.argmax(batch_pred, axis=1)
    # pred_label = tf.gather(tf.convert_to_tensor(CLASS_NAMES), pred_label_index)
    return {
        'prediction': batch_pred,
        'key':key
    }

# @tf.function(input_signature=[tf.TensorSpec([None,], dtype=tf.string)])
# def predict_url(filenames):
#     img_bytes = tf.map_fn(
#         tf.io.read_file,
#         filenames
#     )
#     result = predict_bytes(img_bytes)
#     result['filename'] = filenames
#     return result
# import tensorflow as tf
# import time
# # import joblib
# t = time.time()
model = load_model()
# export_path_sm = "./{}".format(int(t))
# print(export_path_sm)
model.compile(optimizer='adam', loss='binary_crossentropy')

# tf.saved_model.save(model, export_path_sm)
model.save('avl_from_bytes_with_key/',signatures={
    'serving_default': predict_bytes,
    # 'from_url': predict_url
})


# joblib.dump(model, 'avl_model.pkl')
