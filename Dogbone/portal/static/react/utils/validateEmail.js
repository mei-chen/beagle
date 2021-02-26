/**
  *validateEmail
  *
  *if valid email format return true, else false
  *thanks http://stackoverflow.com/a/46181
  */
module.exports = function(email) {
    var re = /^([\w-\+]+(?:\.[\w-]+)*)@((?:[\w-\+]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
    return re.test(email);
}