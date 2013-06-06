$(document).ready(function() {
  'use strict';

  // Package "blf": BibLib Front
  mlab.pkg('blf');

  // Initialize lang and other global assets:
  mlab.pkg('blf.assets');
  blf.assets.lang = 'en';
  blf.assets.languages = [
    {
      id: 'fr',
      labels: {
        fr: 'Français',
        en: 'French'
      }
    },
    {
      id: 'en',
      labels: {
        fr: 'Anglais',
        en: 'English'
      }
    }
  ];

  // Domino global settings:
  domino.settings({
    displayTime: true,
    verbose: true,
    strict: true
  });

  /**
   * First, let's describe our data here. To add a new type, just use:
   *
   *  > if (!domino.struct.isValid('blf.typeTest'))
   *  >   domino.struct.add({
   *  >     id: 'blf.typeTest',
   *  >     struct: {
   *  >       key1: 'string',
   *  >       key2: '?number'
   *  >     }
   *  >   });
   */
  if (!domino.struct.isValid('blf.Dict'))
    domino.struct.add({
      id: 'blf.Dict',
      struct: {
        fr: '?string',
        en: '?string'
      }
    });

  if (!domino.struct.isValid('blf.Property'))
    domino.struct.add({
      id: 'blf.Property',
      struct: {
        multiple: '?boolean',
        property: 'string',
        required: 'boolean',
        type_data: 'string',
        type_ui: 'string',
        labels: '?blf.Dict'
      }
    });

  if (!domino.struct.isValid('blf.Field'))
    domino.struct.add({
      id: 'blf.Field',
      struct: {
        rec_class: 'string',
        rec_type: 'string',
        children: [ 'blf.Property' ]
      }
    });

  /**
   * Controler:
   */
  blf.control = new domino({
    name: 'blf.control',
    properties: [
      // DATA related properties
      {
        value: [],
        id: 'fields',
        type: ['blf.Field'],
        dispatch: 'fieldsUpdated',
        description: 'The field templates.'
      },
      {
        value: {},
        id: 'fieldsTree',
        type: 'object',
        dispatch: 'fieldsTreeUpdated',
        description: 'The fields tree.'
      },
      {
        value: [],
        id: 'creatorRoles',
        type: 'array',
        dispatch: 'creatorRolesUpdated',
        description: 'The creator roles list.'
      },

      // INTERFACE related properties
      {
        value: 'home',
        id: 'mode',
        type: 'string',
        triggers: 'updateMode',
        dispatch: 'modeUpdated',
        description: 'The layout mode (home, search, create).'
      }
    ],
    hacks: [
      {
        // This hack is just useful to make the modules able to log, warn and
        // die trough domino:
        triggers: ['log', 'warn', 'die'],
        method: function(e) {
          this[e.type]((e.data || {}).message);
        }
      },
      {
        triggers: 'loadField',
        method: function(e) {
          this.log('Loading the template of a specific field.');
          this.request('loadField', {
            field: e.data.field
          });
        }
      }
    ],
    services: [
      {
        id: 'loadField',
        description: 'Loads the template of a specified field.',
        url: function(input) {
          return 'templates/' + input.field + '.json';
        },
        success: function(data) {
          var k,
              arr = this.get('fields');

          // If the "rec_type" already exists, it overrides the old one:
          if (this.get('fields').some(function(o) {
            return o.rec_type === data.rec_type;
          }))
            arr = arr.map(function(o) {
              return o.rec_type === data.rec_type ?
                data :
                o;
            });

          // If not, we just push it in our existing fields array:
          else
            arr.push(data);

          // Finally, we update:
          this.update('fields', arr);
        }
      },
      {
        id: 'loadFieldsTree',
        url: 'assets/templates-tree_sample.json',
        setter: 'fieldsTree',
        description: 'Loads the dependance tree of the fields.'
      },
      {
        id: 'loadCreatorRoles',
        url: 'assets/creator-roles.json',
        setter: 'creatorRoles',
        path: 'children',
        description: 'Loads the list of the available creator roles.'
      }
    ]
  });

  // Layout initialization:
  blf.layout = blf.control.addModule(blf.modules.layout);

  // Data initialization:
  blf.control.request(['loadFieldsTree', 'loadCreatorRoles']);
});