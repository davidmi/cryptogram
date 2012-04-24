#!/usr/bin/env python

# TODO(tierney): Last row repair. Instead of writing black, we probably want to
# write an average of the preceeding rows in the block of 8 (due to the JPEG
# DCT). Of course, we must find a way to reengineer this application. Notably,
# the last row will be unrecoverable especially if resizing is involved.

import base64
import numpy
import sys
import logging
import os
from tempfile import NamedTemporaryFile
from Cipher import V8Cipher as Cipher
from json import JSONEncoder, JSONDecoder

from SymbolShape import SymbolShape, four_square, three_square, two_square, \
    one_square, two_by_four, two_by_three, two_by_one
from Codec import Codec
from PIL import Image
from ImageCoder import Base64MessageSymbolCoder, Base64SymbolSignalCoder
import gflags

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format = '%(asctime)-15s %(levelname)8s %(module)10s '\
                      '%(threadName)10s %(thread)16d %(lineno)4d %(message)s')

FLAGS = gflags.FLAGS
gflags.DEFINE_float('wh_ratio', 1.33, 'height/width ratio', short_name = 'r')
gflags.DEFINE_integer('quality', 95,
                      'quality to save encrypted image in range (0,95]. ',
                      short_name = 'q')
gflags.DEFINE_integer('ecc_n', 128, 'codeword length', short_name = 'n')
gflags.DEFINE_integer('ecc_k', 64, 'message byte length', short_name = 'k')
gflags.DEFINE_string('password', None, 'Password to encrypt image with.',
                     short_name = 'p')
gflags.DEFINE_string('symbol_shape', 'two_by_four', 'symbol shape to use',
                     short_name ='s')
gflags.DEFINE_string('image', None, 'path to input image', short_name = 'i')
gflags.DEFINE_string('encrypt', None, 'encrypted image output filename',
                     short_name = 'e')
gflags.DEFINE_string('decrypt', None, 'decrypted image output filename',
                      short_name = 'd')

gflags.MarkFlagAsRequired('password')

_AVAILABLE_SHAPES = {
  'four_square' : four_square,
  'three_square': three_square,
  'two_square' : two_square,
  'one_square' : one_square,
  'two_by_four' : two_by_four,
  'two_by_three' : two_by_three,
  'two_by_one' : two_by_one,
}

class Encrypt(object):
  def __init__(self, image_path, codec, cipher):
    self.image_path = image_path
    self.codec = codec
    self.cipher = cipher

  def _adjust_for_limit(self, dimension_limit):
    pass

  def _image_path_to_encrypted_data(self, image_path):
    with open(image_path, 'rb') as fh:
      raw_image_file_data = fh.read()
    base64_image_file_data = base64.b64encode(raw_image_file_data)
    encrypted_data = self.cipher.encode(base64_image_file_data)

    # TODO(tierney): Strictly using V8Cipher in this code.
    encrypted_data = encrypted_data['iv'] + encrypted_data['salt'] + \
        encrypted_data['ct']

    # Remove base64 artifacts.
    return encrypted_data #.replace('=','')

  def _reduce_image_quality(self, image_path):
    im = Image.open(image_path)
    with NamedTemporaryFile() as fh:
      new_image_path = fh.name + '.jpg'
      im.save(new_image_path, quality=77)
    return new_image_path

  def _reduce_image_size(self, image_path, scale):
    im = Image.open(image_path)
    width, height = im.size
    with NamedTemporaryFile() as fh:
      new_image_path = fh.name + '.jpg'
      im = im.resize((int(width * scale), int(height * scale)))
      width, height = im.size
      # Update codec with the new width, height ratio.
      self.codec.set_wh_ratio(width / float(height))

      im.save(new_image_path, quality=77)
    return new_image_path

  def upload_encrypt(self, dimension_limit = 2048):
    _image_path = self.image_path
    requality_limit = 1
    requality_count = 0
    rescale_count = 0
    logging.info('Encrypting image: %s.' % _image_path)
    while True:
      _ = Image.open(_image_path)
      _w, _h = _.size
      logging.info('Cleartext image dimensions: (%d, %d).' % (_w, _h))
      encrypted_data = self._image_path_to_encrypted_data(_image_path)
      width, height = self.codec.get_prospective_image_dimensions(
        encrypted_data)
      if width <= dimension_limit and height <= dimension_limit:
        break
      logging.info('Dimensions too large (w: %d, h: %d).' % (width, height))

      # Strategies to reduce raw bytes that we need to encrypt: requality,
      # rescale.
      if requality_count < requality_limit:
        logging.info('Requality image.')
        _image_path = self._reduce_image_quality(_image_path)
        requality_count += 1
      else:
        rescale_count += 1
        logging.info('Rescale with original image.')
        _image_path = self._reduce_image_size(self.image_path,
                                              1.0-(0.05 * rescale_count))
    return encrypted_data

  def encrypt(self):
    image = Image.open(self.image_path)
    with open(self.image_path, 'rb') as fh:
      raw_image_file_data = fh.read()
    base64_image_file_data = base64.b64encode(raw_image_file_data)
    encrypted_data = cipher.encode(base64_image_file_data)
    width, length = self.codec.get_prospective_image_dimensions()



# def main(argv):
#   logging.info(argv)

#   passed_values = argv[1:]
#   for passed_value in passed_values:
#     if os.path.isdir(passed_value):
#       logging.info('Treat %s like a directory.' % passed_value)
#     else:
#       logging.info('Treat %s like a file.' % passed_value)


def main(argv):
  try:
    argv = FLAGS(argv)  # parse flags
  except gflags.FlagsError, e:
    print '%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  symbol_shape = _AVAILABLE_SHAPES[FLAGS.symbol_shape]

  wh_ratio = FLAGS.wh_ratio
  quality = FLAGS.quality

  cipher = Cipher(FLAGS.password)
  codec = Codec(symbol_shape, wh_ratio, Base64MessageSymbolCoder(),
                Base64SymbolSignalCoder())

  if FLAGS.image and FLAGS.encrypt:
    logging.info('Image to encrypt: %s.' % FLAGS.image)

    # Update codec based on wh_ratio from given image.
    _image = Image.open(FLAGS.image)
    _width, _height = _image.size
    wh_ratio = _width / float(_height)
    codec.set_wh_ratio(wh_ratio)

    # Determine file size.
    with open(FLAGS.image,'rb') as fh:
      orig_data = fh.read()
      length = fh.tell()
      logging.info('Image filesize: %d bytes.' % length)

    crypto = Encrypt(FLAGS.image, codec, cipher)
    encrypted_data = crypto.upload_encrypt()
    logging.info('Encrypted data length: %d.' % len(encrypted_data))
    im = codec.encode(encrypted_data)

    logging.info('Saving encrypted jpeg with quality %d.' % quality)
    im.save(FLAGS.encrypt, quality=quality)
    with open(FLAGS.encrypt) as fh:
      fh.read()
      logging.info('Encrypted image size: %d bytes.' % fh.tell())
      logging.info('Encrypted image data expansion %.2f.' % \
                     (fh.tell() / float(length)))

  if not FLAGS.decrypt:
    return

  if FLAGS.image and FLAGS.encrypt and FLAGS.decrypt:
    read_back_image = Image.open(FLAGS.encrypt)
  elif FLAGS.image and not FLAGS.encrypt and FLAGS.decrypt:
    logging.info('Reading message we did not encrypt.')
    with open(FLAGS.image, 'rb') as fh:
      fh.read()
      logging.info('Encrypted image filesize: %d.' % fh.tell())

    read_back_image = Image.open(FLAGS.image)
    _width, _height = read_back_image.size
    wh_ratio = _width / float(_height)
    codec = Codec(symbol_shape, wh_ratio, Base64MessageSymbolCoder(),
                  Base64SymbolSignalCoder())

  binary_decoding = codec.decode(read_back_image)

  if FLAGS.encrypt and FLAGS.decrypt:
    logging.info('Byte for byte diff: %d.' % \
                   byte_for_byte_compare(encrypted_data, binary_decoding))

  # Required "un"-filtering to base64 data.
  def _base64_pad(s):
    mod = len(s) % 4
    if mod == 0: return s
    return s + (4 - mod) * '='

  # padded_decoding = _base64_pad(binary_decoding)
  _pad = 3

  _iv = binary_decoding[0:22]
  _salt = binary_decoding[22:33]
  _ct = binary_decoding[33:]
  decoded = {'iv': _iv, 'salt': _salt, 'ct': _ct}
  json_str = JSONEncoder().encode(decoded)

  decrypted_decoded = cipher.decode(json_str)
  # with open('decrypted.base64.txt', 'w') as fh:
  #   fh.write(decrypted_decoded)
  extracted_data = base64.b64decode(decrypted_decoded)

  if FLAGS.image and FLAGS.decrypt:
    with open(FLAGS.decrypt, 'wb') as fh:
      fh.write(extracted_data)
    logging.info('Saved decrypted file: %s.' % FLAGS.decrypt)


def byte_for_byte_compare(a, b):
  errors = 0
  for i, datum in enumerate(a[:min(len(a), len(b))]):
    if datum != b[i]:
      errors += 1
  if len(b) > len(a):
    errors += len(b) - len(a)
  return errors

if __name__=='__main__':
  main(sys.argv)