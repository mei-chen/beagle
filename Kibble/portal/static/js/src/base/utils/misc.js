/**
 * Constructs FormData
 * @param dict
 * @returns {Object} FormData ready to send
 */
export const formDataFrom = (dict) => {
  let formData = new FormData();
  for (let [key, value] of Object.entries(dict)) {
    formData.append(key, value)
  }
  return formData
};

export const capitalize = (string) => {
  return string[ 0 ].toUpperCase() + string.slice(1)
};


/***
 * Move element from one Immutable.js list to another
 * @param {List} src
 * @param {List} dst
 * @param {function} predicate
 * @returns {Array}
 */
export const transferTo = (src, dst, predicate) => {
  dst = dst.withMutations((list) => {
    src = src.filter((el) => {
      if (!predicate(el)) {
        list.push(el);
        return false
      } else {
        return true
      }
    });
    return list
  });
  return [ src, dst ]
};

/**
 * Search in an Array of Objects
 * @param {List|Array} haystack
 * @param {string} field Object key
 * @param {string} needle Object value
 * @param {boolean} icase Case sensitivity
 * @returns {List|Array}
 */
export const filterObjects = (haystack, field, needle, icase = true) => {
  if (icase) {
    return haystack.filter((el) => {
      return !el || el[ field ].toLowerCase().indexOf(needle.toLowerCase()) !== -1
    })
  } else {
    return haystack.filter(el => !el || el[ field ].indexOf(needle) !== -1)
  }
};

/**
 * Like in python
 * more about type conversion http://jibbering.com/faq/notes/type-conversion/
 * @param args
 * @returns {boolean}
 */
export const all = (...args) => {
  return args.every((el) => {
    return !!el
  })
};


export const updateEntry = (haystack, newObject, predicate) => {
  return haystack.map(obj => {
    if (predicate(obj)) {
      return newObject
    }
    return obj
  })
};


export const getFirst = (haystack, predicate) => {
  for (const obj of haystack) {
    if (predicate(obj)) return obj
  }
};
