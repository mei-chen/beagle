var THREE_CHAR_MONTH = {
  0: 'Jan',
  1: 'Feb',
  2: 'Mar',
  3: 'Apr',
  4: 'May',
  5: 'Jun',
  6: 'Jul',
  7: 'Aug',
  8: 'Sep',
  9: 'Oct',
  10: 'Nov',
  11: 'Dec'
};


exports.formatDate = function(date) {
  date = date || new Date();
  var day = date.getDate();
  var month = THREE_CHAR_MONTH[date.getMonth()];
  var year = date.getFullYear();
  return '' + day + '-' + month + '-' + year;
};
