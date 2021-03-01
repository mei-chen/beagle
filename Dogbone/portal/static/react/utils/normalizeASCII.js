/* Convert some of the various visually similar
* characters to those that a keyboard enters
*/

module.exports = function(str) {
    str = str.replace(new RegExp("[\“\”]", "g"),"\"");
    str = str.replace(new RegExp("[\-\—\–]", "g"),"\-");
    return str;
}
