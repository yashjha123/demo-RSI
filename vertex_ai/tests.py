import tensorflow as tf
img = "https://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A33304-2019-01-12_07_48_36.jpg"
# @tf.function(input_signature=[tf.TensorSpec([None,], dtype=tf.string)])
def download(imgs): 
    import requests
    from PIL import Image
    from io import BytesIO
    map(lambda x:Image.open(BytesIO(requests.get(imgs).content)),imgs)
    # response = requests.get(img_url)
    # image = 

    print(tf.io.read_file(origin=imgs[0]))
    # d = tf.map_fn(
    #     tf.keras.utils.get_file,
    #     img
    # )
# d = tf.keras.utils.get_file(origin=)
print(download([img]))