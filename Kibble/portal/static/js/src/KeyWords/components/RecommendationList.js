import React from 'react';
import { ListGroup, ListGroupItem } from 'react-bootstrap';

import "../scss/RecommendationList.scss"

const RecommendationItem = ({ word, index, style, handleSelect }) => {
  return <ListGroupItem
    title={word}
    bsStyle={style}
    onClick={() => handleSelect(index)}
  >
    {word}
  </ListGroupItem>
 };

const RecommendationList = ({ keywords, label, noKeyWords, markKeyword }) => {
  return (
      <div className="keyword-list-selector">
        <h4 className="selector-header">{label}</h4>
        <ListGroup bsClass="list-group-class">
          {!keywords.size && (<div>{noKeyWords}</div>)}
          {keywords.map((keyword, i) => {
             return <RecommendationItem
                key={i}
                index={i}
                word={keyword.text}
                style={keyword.status}
                handleSelect={() => markKeyword(i)}
              />
          })}
        </ListGroup>
      </div>
  );
};

export default RecommendationList;
