module.exports =
  title: "Teleport"
  sectionOrder: ["home", "python", "spec"]
  sections:
    home:
      title: "About"
      star: true
      repoLink: true
      subMenuShow: false
    python:
      title: "Python"
      star: true
      repoLink: true
      subMenuShow: true
      subMenu: [
        { version: 'latest' }
        { divider: true }
        { version: '0.2' }
        { version: '0.1' }
      ]
    spec:
      title: "Specification"
      star: true
      repoLink: true
      subMenuShow: true
      subMenu: [
        { version: 'latest' }
        { divider: true }
        { version: '1.0' }
      ]
    archive: [
      'spec-old'
    ]
  build:
    archive: [
      'spec-old'
    ]
    checkouts: [
      'master'
      '0.1-maintenance'
      '0.2-maintenance'
    ]
    subdirs:
      'checkouts-master': ['python']
      'checkouts-0.1-maintenance': ['python']
      'checkouts-0.2-maintenance': ['python']
    sphinx: [
      'checkouts-master-python'
      'checkouts-0.1-maintenance-python'
      'checkouts-0.2-maintenance-python'
    ]
    layout:
      python:
        '0.1':
          content: 'checkouts-0.1-maintenance-python-sphinx'
          jquery: true
        '0.2':
          content: 'checkouts-0.2-maintenance-python-sphinx'
          jquery: true
        'latest':
          content: 'checkouts-master-python-sphinx'
          jquery: true
       spec:
        '1.0':
          content: 'archive-spec-old'
          jquery: true
        'latest':
          content: 'spec-new'
          nobs: true
