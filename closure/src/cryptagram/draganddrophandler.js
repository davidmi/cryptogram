// Drag and drop handler class for processing the incoming images for the
// Cryptagram pipeline. This class only manipulates the filenames. It will
// mitigate the pressure on the system by waiting on CustomEvents that will
// trigger that the pipeline is able to support another image.

goog.provide('cryptagram.DragAndDropHandler');

goog.require('goog.debug.Console');
goog.require('goog.debug.Logger');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.events.FileDropHandler');
goog.require('goog.events.EventType');
goog.require('goog.events.EventTarget');

goog.require('cryptagram.RemoteLog');
goog.require('cryptagram.cipher');
goog.require('cryptagram.codec.bacchant');
goog.require('cryptagram.container');
goog.require('cryptagram.decoder');
goog.require('cryptagram.encoder');
goog.require('cryptagram.encoder.EventType');
goog.require('cryptagram.encoder.EncoderEvent');
goog.require('cryptagram.loader');

// Constructor.
cryptagram.DragAndDropHandler = function () {
  document.body.innerHTML += cryptagram.templates.demo();

  goog.events.listen(goog.dom.getElement('encrypt_link'),
                     goog.events.EventType.CLICK, this.showEncrypt, false, this);

  var logconsole = new goog.debug.Console();
  logconsole.setCapturing(true);
}

// Logger naming for pretty log message prefixes.
cryptagram.DragAndDropHandler.prototype.logger =
  goog.debug.Logger.getLogger('cryptagram.DragAndDropHandler');

// Exposes the hook to start the encoding process.
cryptagram.DragAndDropHandler.prototype.showEncrypt = function () {
  var self = this;
  goog.dom.getElement('main').innerHTML = cryptagram.templates.encrypt();

  var selector = goog.dom.getElement('file_selector');
  goog.events.listen(selector,
                     goog.events.EventType.CHANGE,
                     function(e) {
                       self.handleFiles(e.target.files);
                     },
                     false,
                     self);

  var dropZone = goog.dom.getElement('drop_zone');
  var handler = new goog.events.FileDropHandler(dropZone, true);
  goog.events.listen(handler,
                     goog.events.FileDropHandler.EventType.DROP,
                     function(e) {
                       var files = e.getBrowserEvent().dataTransfer.files;
                       self.handleFiles(files);
                     });

  this.downloadify = Downloadify.create('downloadify', {
    filename: "encrypted.zip",
    data: function(){
      return self.zip.generate();
    },
    onError: function(){
      alert('Nothing to save.');
    },
    dataType: 'base64',
    swf: 'media/downloadify.swf',
    downloadImage: 'images/download.png',
    width: 100,
    height: 30,
    transparent: false,
    append: false,
    enabled: true
  });
};

// Main hook for starting the encoding process. This method should mitigate how
// the data is traversing the pipeline. In particular, we should only allow one
// image through the encoding pipeline at a time. Also, we must cancel the event
// that bubbles to this portion of the code so that we do not bother the rest of
// the ecosystem.
cryptagram.DragAndDropHandler.prototype.handleFiles = function (files) {
  // Files is a FileList of File objects. List some properties.
  var output = [];
  var zip;
  var self = this;

  if (this.zip == null) {
    this.zip = new JSZip();
    this.images = this.zip.folder('images');
    this.numberImages = 0;
  }

  var numFiles = files.length;
  var completed = 0;

  var encoder = new cryptagram.encoder();
  goog.events.listen(encoder, "IMAGE_DONE", function (event) {
    console.log ("Got a message back with this much dat: " + event.dat.length);
    completed++;
    self.images.file(completed + '.jpg',
                     event.dat,
                     { base64: true });
    event.preventDefault();
    event.stopPropagation();

    if (completed < numFiles) {
      console.log("More to go!");
      encoder.startEncoding(files[completed]);
    } else {
      // TODO(tierney): Downloadify kick start?
    }
  },
										true,
										this);

  encoder.startEncoding(files[completed]);
  console.log("Going out of scope.");
};


cryptagram.DragAndDropHandler.show_error = function(msg, url, linenumber) {
  console.log('Error message: '+msg+'\nURL: '+url+'\nLine Number: '+linenumber);
  return true;
};

goog.exportSymbol('cryptagram.DragAndDropHandler', cryptagram.DragAndDropHandler);
goog.exportSymbol('cryptagram.DragAndDropHandler.prototype.showEncrypt',
                  cryptagram.DragAndDropHandler.prototype.showEncrypt);

