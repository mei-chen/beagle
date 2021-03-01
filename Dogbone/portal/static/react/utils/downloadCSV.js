var assign = require('object-assign');
var CSV = require('comma-separated-values');
var replaceLineBreak = require('./replaceLineBreak');

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


function formatDate(date) {
  date = date || new Date();
  var day = date.getDate();
  var month = THREE_CHAR_MONTH[date.getMonth()];
  var year = date.getFullYear();
  return '' + day + '-' + month + '-' + year;
};


/**
 * getCSVString
 * generates a CSV representation of the clause table
 *
 * @return {string} the CSV string
 */
function getCSVString(sentences, title, created, user, parties) {

  // getting pretty text for a label
  var niceLabel = {
    'RESPONSIBILITY': 'Responsibility',
    'LIABILITY': 'Liability',
    'TERMINATION': 'Termination'
  };

  //dummy row
  var dummyRow = {
    //clause : '',
    involvedParties: '',
    allTags: '',
    commenter: '',
    comment: ''
  };

  var csvArray = [];

  //Build Header
  //title
  var row1 = assign({ clause: title}, dummyRow);
  csvArray.push(row1);
  // //upload date
  var row2 = assign({ clause: "Uploaded: " + created}, dummyRow);
  csvArray.push(row2)
  // //export date
  var row3 = assign({ clause: "Exported: " + new Date()}, dummyRow);
  csvArray.push(row3)
  // //exported by
  var name = (user.first_name && user.last_name) ? user.first_name + ' ' + user.last_name : user.email;
  var row4 = assign({ clause: "Exported By: " + name}, dummyRow);
  csvArray.push(row4)
  // //spacing
  var row5 = assign({ clause: ""}, dummyRow);
  csvArray.push(row5)
  //header row
  csvArray.push({
    clause: 'Clause',
    involvedParties: 'Involved Part(y/ies)',
    allTags: 'Tags',
    commenter: 'Commenter',
    comment: 'Comment'
  });

  sentences.forEach(sentence => {
    sentence.form = replaceLineBreak(sentence.form, " ");

    //annotations
    var annotations = sentence.annotations || [];

    //involved parties
    var involvedParties = [];
    if (annotations.length > 0) {
      // generates an array like ["Blackfoot", "You", "Both"]
      involvedParties = annotations.map(a => {
        const party = parties[a.party] || {};
        return party.name || a.party;
      });
    }

    //analysis tags
    var allTags = [];
    if (annotations.length > 0) {
      // generates an array like ["Blackfoot", "You", "Both"]
      allTags = annotations.map(a => a.label);
    }

    //TODO: Online Learner Tags (Auto Analysis)


    //comments/ commenters
    var comments = sentence.comments;
    var firstCommenter = '';
    var firstComment = '';
    if (comments) {
      comments = comments.reverse(); //flip into chronological order
      firstCommenter = comments[0].author.first_name + ' ' + comments[0].author.last_name;
      firstComment = comments[0].message;

      //if there is more than 1 comment, build an array of table rows to inject after main row
      if (comments.length > 1) {
        //slice off the first comment
        comments = comments.slice(1);
        //create comment rows
        var commentRows = comments.map( comment => {
          // generates a table row
          return {
            clause: '',
            involvedParties: '',
            allTags: '',
            commenter: comment.author.first_name + ' ' + comment.author.last_name,
            comment: comment.message
          };
        });
      }
    }

    // generates a table row
    var tableRow = {
      clause: sentence.form,
      involvedParties: involvedParties.join(', '),
      allTags: allTags.join(', '),
      commenter: firstCommenter,
      comment: firstComment
    };
    // adds the row to the CSV array
    csvArray.push(tableRow);

    //add extra comments
    if (commentRows) {
      commentRows.forEach( commentRow => {
        csvArray.push(commentRow);
      });
    }
  });

  var csv = new CSV(csvArray);
  var encoded = csv.encode();
  return encoded;
}


/**
 * downloadCSV()
 *
 * Generates and invokes browser download of a CSV file comprised of
 * Beagle sentence objects
 *
 */
module.exports = function(sentences, title, created, user, parties) {
  Intercom('trackUserEvent', 'export-csv');
  var emailSlug = user.email.split('@')[0];
  var truncTitle = title.substring(0, 10).trim().replace(' ', '-');
  var dateStr = formatDate();
  var fileName = `${emailSlug}-${truncTitle}-${dateStr}`.toLowerCase();
  var uriHeader = "data:text/csv;charset=utf-8,";
  var csvString = getCSVString(sentences, title, created, user, parties);
  var encodedUri = encodeURI(uriHeader + csvString);
  // create invisible link and force click to download
  var link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `${fileName}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
