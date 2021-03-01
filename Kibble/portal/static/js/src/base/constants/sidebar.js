import { urls } from 'base/constants/constants';


// Sidebar config/items to show
// activeForUrls violates dry but w/o it we have to dig through array each time when componentWillMount
// and onSideBarClick event
// You can omit subMenuItems and activeForUrls (fallback to url then)
export const sideBarItems = [
  {
    // Title of the top item
    title: 'Upload',
    // URL to open by clicking on top item
    url: urls.LOCAL_FOLDER,
    // Submenu will be shows if browser url matches to any of this
    activeForUrls: [ '/', urls.LOCAL_FOLDER, urls.ONLINE_FOLDER ],
    // Submenu items
    subMenuItems: [
      { title: 'Local Folder', url: urls.LOCAL_FOLDER },
      { title: 'Online Folder', url: urls.ONLINE_FOLDER }
    ]
  },
  {
    title: 'Batch management',
    url: urls.PROJECT_MANAGEMENT,
    activeForUrls: [ urls.PROJECT_MANAGEMENT, urls.BATCH_MANAGEMENT ],
    subMenuItems: [
      { title: 'Project Management', url: urls.PROJECT_MANAGEMENT },
      { title: 'Batch Management', url: urls.BATCH_MANAGEMENT },
    ]
  },
  {
    title: 'Pre-process',
    url: urls.IDENTIFIABLE_INFORMATION,
    activeForUrls: [ urls.IDENTIFIABLE_INFORMATION, urls.OCR, urls.FORMAT_CONVERTING, urls.CLEANUP_DOCUMENT, urls.SENTENCE_SPLITTING ],
    subMenuItems: [
      { title: 'Identifiable Information', url: urls.IDENTIFIABLE_INFORMATION },
      //{ title: 'OCR', url: urls.OCR }, // Remove for now
      { title: 'Format Converting', url: urls.FORMAT_CONVERTING },
      { title: 'Cleanup Document', url: urls.CLEANUP_DOCUMENT },
      { title: 'Sentence Splitting', url: urls.SENTENCE_SPLITTING }
    ]
  },
  {
    title: 'Sentence',
    url: urls.SENTENCES,
    activeForUrls: [ urls.SENTENCES, urls.KEY_WORDS, urls.REG_EX, urls.SENTENCES_OBFUSCATION ],
    subMenuItems: [
      { title: 'Sentence Pulling', url: urls.SENTENCES },
      { title: 'Key Words', url: urls.KEY_WORDS },
      { title: 'Reg Ex', url: urls.REG_EX },
      { title: 'Sentences Obfuscation', url: urls.SENTENCES_OBFUSCATION }
    ]
  },
  {
    title: 'Settings',
    url:urls.SETTINGS,
  }
];
