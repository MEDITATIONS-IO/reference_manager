;(function() {
  'use strict';

  mlab.pkg('blf.modules');

  blf.modules.layout = function() {
    domino.module.call(this);

    var _self = this,
        _html = $('#layout'),
        _nav = $('#nav', _html),
        _panels = $('#panels', _html),
        _modules = [];

    // Bind search:
    function simpleSearch() {
      _self.dispatchEvent('search', {
        query: $('#simple-entries-search', _nav).val()
      });
    }

    $('button[data-action="search"]', _nav).click(simpleSearch);
    $('#simple-entries-search', _nav).keypress(function(e) {
      if (e.which === 13)
        simpleSearch();
    });

    // Bind navigation:
    $('button[data-mode]', _nav).click(function() {
      _self.dispatchEvent('updateMode', {
        mode: $(this).data('mode')
      });
    });

    // Initialize other modules:
    _modules.push(blf.control.addModule(
      blf.modules.fieldsPanel,
      [ $('[data-panel="fields"]', _panels) ]
    ));

    _modules.push(blf.control.addModule(
      blf.modules.createPanel,
      [ $('[data-panel="create"]', _panels) ]
    ));

    _modules.push(blf.control.addModule(
      blf.modules.listPanel,
      [ $('[data-panel="list"]', _panels) ]
    ));

    _modules.push(blf.control.addModule(
      blf.modules.advancedSearchPanel,
      [ $('[data-panel="advancedSearch"]', _panels) ]
    ));

    // Listen to the controller:
    this.triggers.events.modeUpdated = function(d) {
      var mode = d.get('mode');
      $('[data-panel]:not([data-panel="' + mode + '"])', _panels).css('display', 'none');
      $('[data-panel="' + mode + '"]', _panels).css('display', '');
    };
  };
})();
