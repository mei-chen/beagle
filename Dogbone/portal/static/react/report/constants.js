var ChangeTypes = {
  MODIFY: 'MODIFY',
  DELETE: 'DELETE',
  ADD: 'ADD'
};

var TrackChanges = {
  SEE_CHANGES: 'SEE_CHANGES',
  SHOW_ORIGINAL: 'SHOW_ORIGINAL',
  ONLY_CHANGES: 'ONLY_CHANGES'
};

var UserEvents = {
  OPEN_WIDGET_VIEW: 'open_widget_view',
  OPEN_CONTEXT_VIEW: 'open_context_view',
  OPEN_DETAIL_VIEW: 'open_detail_view',
  OPEN_CLAUSE_VIEW: 'open_clause_view'
}

module.exports = {
  ChangeTypes,
  TrackChanges,
  UserEvents
};
