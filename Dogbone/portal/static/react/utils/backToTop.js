var $ = require('jquery');

/*
* animate the page as a scroll back to the top
*/
module.exports = function(sentences, title, created, user) {
  $('html, body').animate({
    // back to the top son
    scrollTop: 0
  });
}