module.exports =
  title: "Teleport"
  sectionOrder: ["python", "spec"]
  sections:
    python:
      title: "Python"
      github: "teleport.py"
      star: true
      repoLink: true
      checkouts: [
        { version: '0.2', branch: '0.2-maintenance' }
        { version: '0.1', branch: '0.1-maintenance' }
      ]
    spec:
      title: "Specification"
      github: "teleport-spec"
      star: false
      repoLink: true
      checkouts: [
        { version: '1.0', branch: '1.0-maintenance' }
      ]
