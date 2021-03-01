/*
* given two arrays of objects and a compare function, this returns the
* interesection.
*
*
* @param [{object}] arrayA - Object array one.
* @param [{object}] arrayB - Object array two.
* @param function compareFunction - the compare function({object1}, {object2}) 
*                                   returning if the objects are indeed intersections.
* return - Array
*/

module.exports = function intersectionArrayOfObjects(arrayA, arrayB, compareFunction) {
  return arrayA.filter(elementA => {
    var match = false;
    arrayB.forEach(elementB => {
      if (compareFunction(elementA, elementB)) {
        match = true;
      }
    });
    return match
  });
}