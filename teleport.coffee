root = 1

# If no framework is available, just export to the global object (window.HUSL
# in the browser)
@HUSL = root unless module? or jQuery? or requirejs?
# Export to Node.js
module.exports = root if module?
# Export to jQuery
jQuery.husl = root if jQuery?
# Export to RequireJS
define(root) if requirejs? and define?