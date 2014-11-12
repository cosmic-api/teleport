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
  build:
    archive: [
      'spec-old'
    ]
    checkouts: [
      {branch: 'master'}
      {branch: 'py-0.1-maintenance'}
      {branch: 'py-0.2-maintenance'}
      {tag: 'spec-draft-00'}
    ]
    sphinx: [
      'checkouts-master'
      'checkouts-py-0.1-maintenance'
      'checkouts-py-0.2-maintenance'
      'current-source'
    ]
    xml2rfc: [
      'checkouts-master'
      'checkouts-spec-draft-00'
    ]
    layout:
      python:
        '0.1':
          content: 'checkouts-py-0.1-maintenance-sphinx'
          jquery: true
        '0.2':
          content: 'checkouts-py-0.2-maintenance-sphinx'
          jquery: true
        'latest':
          content: 'checkouts-master-sphinx'
          jquery: true
       spec:
        'latest':
          content: 'checkouts-master-xml2rfc'
          nobs: true
        'draft-00':
          content: 'checkouts-spec-draft-00-xml2rfc'
          nobs: true
        '1.0':
          content: 'archive-spec-old'
          jquery: true
