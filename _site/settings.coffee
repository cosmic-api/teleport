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
  inject:
    'checkouts-master-python-sphinx':
      section: 'python'
      version: 'latest'
      jquery: true
    'checkouts-0.1-maintenance-python-sphinx':
      section: 'python'
      version: '0.1'
      jquery: true
    'checkouts-0.2-maintenance-python-sphinx':
      section: 'python'
      version: '0.2'
      jquery: true

