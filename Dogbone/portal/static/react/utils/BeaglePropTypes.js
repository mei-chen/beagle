/**
 * BeaglePropTypes
 *
 * Some React prop validators we use for Beagle
 *
 * @author glifchits
 */

module.exports = {

  /**
   * nullOrDefined
   *
   * Specifies a prop which is either null or defined.
   *
   * @param props
   * @param propName
   * @param componentName
   */
  nullOrDefined(props, propName, componentName) {
    var prop = props[propName];
    var isNull = typeof prop === 'object' && prop === null;
    var isUndefined = typeof prop === 'undefined' && prop === undefined;
    if (!isNull && isUndefined) {
      return new Error('Prop `' + propName + '` for `' + componentName + '` was undefined.');
    }
  }

};
