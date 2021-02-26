/*
 * objToUri
 *
 * Serializes a plain Javascript object to a URI encoded string
 *
 * thanks to
 * http://stackoverflow.com/a/1714899/818492
 *
 */
/* eslint-disable */
let serialize = function(obj, prefix) {
  let str = [];
  for (let p in obj) {
    if (obj.hasOwnProperty(p)) {
      let k = prefix ? prefix + "[" + p + "]" : p;
      let v = obj[p];
      str.push(typeof v == "object" ?
               serialize(v, k) :
               encodeURIComponent(k) + "=" + encodeURIComponent(v));
    }
  }
  return str.join("&");
}

module.exports = serialize;
