
//Housekeeping: clear away the introJs object state varible when done with it.
const removeIntroJsState = context => {
    context.setState({ introJsObject : null });
  };

//if there is an active introJs wizard, we must kill it if the user interacts with the contents
// inside the widget panel.
export const killIntroJsWizard = () => {
  if (!!this.state.introJsObject) {
    context.state.introJsObject.exit();
  }
}

  //Starts the overlay intro wizard
export const introJsWidgetViewEvoke = context => {
  //if the scripts are in the Template, then this is the user's first visit
  if (typeof introJs !== 'undefined' && !INTROJS_STEPS_WIDGET_VIEW_DONE) {
    var intro = introJs();
    intro.setOptions(INTROJS_STEPS_WIDGET_VIEW);
    intro.oncomplete(context.removeIntroJsState);
    intro.onexit(context.removeIntroJsState);
    intro.start();
    context.setState({ introJsObject : intro });
    INTROJS_STEPS_WIDGET_VIEW_DONE = true; //set the steps to be completed so not to show again this session.
  }
};
