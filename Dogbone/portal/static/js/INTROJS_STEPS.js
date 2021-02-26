//-----------------
// Widget View Steps
//-----------------
var INTROJS_STEPS_WIDGET_VIEW = {
    exitOnOverlayClick: false,
    showStepNumbers: false,
    steps: [
        {
            intro: "<i class='fa fa-gear'></i><div class='introjs-title'>Welcome to the Report Page!</div><div class='introjs-subtext'>Click 'Next' to see how easy Beagle makes reviewing a contract.</div>",
            tooltipClass: "intro-window"
        },
        {
            element: '#step1',
            intro: "The Widget View is a snapshot of your contract. Click any of the icons to explore different views.",
            position: 'right',
            highlightClass: 'intro-sidebar'
        },
        {
            element: '#step2',
            intro: "<div>We start by identifying the 2 parties. If you don't agree with us, click <i class='fa fa fa-pencil-square-o'></i> to change them.</div>",
            position: 'bottom',
            highlightClass: 'intro-party-highlight',
            tooltipClass: 'intro-party-tooltip'
        },
        {
            element: '#step3',
            intro: "<div>Beagle comes trained to sniff out the key clauses for both parties.</div><br></br> <div>Click on any of the graphs to dive into the contract and see the clauses we've found.</div>",
            position: 'left',
            tooltipClass: "intro-widgets-tooltip",
        },
    ]
}
var INTROJS_STEPS_WIDGET_VIEW_DONE = false;

//-----------------
// Clause Table Steps
//-----------------
var INTROJS_STEPS_CLAUSE_TABLE = {
    exitOnOverlayClick: false,
    showStepNumbers: false,
    steps: [
        {
            intro: "<i class='fa fa-list-alt'></i><div class='introjs-title'>Clause Table</div><div class='introjs-subtext'>Find and organize keywords and clauses in seconds</div><br></br><div class='introjs-subtext-2'>For more training on the Clause Table click <a href='http://docs.beagle.ai/doc/clause-table.html'>here.</a></div>",
            tooltipClass: "intro-window"
        },
        {
            element: '#ct-step1',
            intro: "Start typing here to see a list of all clauses containing your terms.",
            position: 'top'
        },
        {
            element: '#ct-step2',
            intro: "Filter tags, revisions, comments and likes here.",
            position: 'bottom'
        },
    ]
}
var INTROJS_STEPS_CLAUSE_TABLE_DONE = false;


//-----------------
// Context View Steps
//-----------------
var INTROJS_STEPS_CONTEXT_VIEW = {
    exitOnOverlayClick: false,
    showStepNumbers: false,
    steps: [
        {
            intro: "<i class='fa fa-columns'></i><div class='introjs-title'>Context View</div><div class='introjs-subtext'>All the clauses Beagle found are here on the left. Click one to scroll through the contract and see it highlighted on the right</div><br></br><div class='introjs-subtext-2'>For more training on the Context View click <a href='http://docs.beagle.ai/doc/context-view.html'>here.</a></div>",
            tooltipClass: "intro-window"
        },
        {   element: "#cv-step1",
            intro: "<div>To edit, red-line or collaborate click on a sentence.</div>",
            position: 'left'
        }
    ]
}
var INTROJS_STEPS_CONTEXT_VIEW_DONE = false;



//-----------------
// Editor Box Steps
//-----------------
var INTROJS_STEPS_EDITOR_BOX = {
    exitOnOverlayClick: false,
    showStepNumbers: false,
    steps: [
        {
            element: '#eb-step2',
            intro: 'Make simple edits and redlines here in the editor box.',
            position: 'top',
            highlightClass: 'intro-editor-box-highlight'
        },
        {
            element: '#eb-step3',
            intro: 'Organize and tag clauses by subject or function, and train Beagle what’s important to your business. ',
            position: 'bottom',
        },
        {
            element: '#eb-step4',
            intro: 'Ask others to review and for feedback.',
            position: 'top',
        }

    ]
}
var INTROJS_STEPS_EDITOR_BOX_DONE = false;

//-----------------
// Detail View Steps
//-----------------
var INTROJS_STEPS_DETAIL_VIEW = {
    exitOnOverlayClick: false,
    showStepNumbers: false,
    showBullets: false,
    steps: [
        {
            intro: "<i class='fa fa-file-text-o'></i><div class='introjs-title'>Detail View</div><div class='introjs-subtext'>See the whole contract highlighted. Anything <span style='background-color: #ffd4dc;'>pink</span> is a responsibility, <span style='background-color: #b6daf2;'>blue</span> a liability and <span style='background-color: #ffffb3;'>yellow</span> a termination clause.</div>",
            tooltipClass: "intro-window"
        },
    ]
}
var INTROJS_STEPS_DETAIL_VIEW_DONE = false;
