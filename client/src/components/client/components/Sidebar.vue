<template>
  <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
    <div style="height:calc(100% - 36px)">
      <v-select :disabled="loadingServer || databaseItems.length == 0" v-model="database" @change="getObjects" solo :items="databaseItems" label="Database" hide-details background-color="#303030" height="48px" style="padding:10px;"></v-select>
      <div v-if="treeviewMode == 'servers' || database.length != 0" class="subtitle-2" style="padding-left:10px; padding-top:8px; padding-bottom:8px; color:rgb(222,222,222);">{{ (treeviewMode == 'servers') ? 'SERVERS' : 'OBJECTS' }}</div>
      <div v-else-if="database.length == 0" class="body-2" style="padding-left:20px; padding-top:10px; padding-bottom:7px; color:rgb(222,222,222);"><v-icon small style="padding-right:10px; padding-bottom:4px;">fas fa-arrow-up</v-icon>Select a database</div>
      <v-progress-circular v-if="loading" indeterminate size="20" width="2" style="margin-top:2px; margin-left:12px;"></v-progress-circular>
      <div v-else-if="treeviewMode == 'servers' || database.length > 0" style="height:100%">
        <v-treeview @contextmenu="showContextMenu" :active.sync="treeview" item-key="id" :open="treeviewOpened" :items="treeviewItems" :search="treeviewSearch" activatable open-on-click transition class="clear_shadow" style="height:calc(100% - 162px); width:100%; overflow-y:auto;">
          <template v-slot:label="{item, open}">
            <v-btn text @click="treeviewClick(item)" @contextmenu="showContextMenu" style="font-size:14px; text-transform:none; font-weight:400; width:100%; justify-content:left; padding:0px;"> 
              <v-icon v-if="!item.type" small style="padding:10px;">
                {{ open ? 'mdi-folder-open' : 'mdi-folder' }}
              </v-icon>
              <v-icon v-else small :title="item.type" :color="treeviewColor[item.type]" style="padding:10px;">
                {{ treeviewImg[item.type] }}
              </v-icon>
              {{item.name}}
              <v-spacer></v-spacer>
              <v-progress-circular v-if="loadingServer && item.id == treeview[0]" indeterminate size="16" width="2" color="white" style="margin-right:10px;"></v-progress-circular>
            </v-btn>
          </template>
        </v-treeview>
        <v-menu v-model="showMenu" :position-x="x" :position-y="y" absolute offset-y>
          <v-list style="padding:0px;">
            <v-list-item v-for="menuItem in menuItems" :key="menuItem" @click="clickAction">
              <v-list-item-title>{{menuItem}}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
        <v-text-field v-if="treeviewItems.length > 0" :disabled="treeviewMode == 'objects' && database.length == 0" v-model="treeviewSearch" label="Search" dense solo hide-details height="38px" style="float:left; width:100%; padding:10px;"></v-text-field>
      </div>
    </div>
    <!--------------------->
    <!-- LEFT BOTTOM BAR -->
    <!--------------------->
    <!-- SERVERS -->
    <div v-if="treeviewMode == 'servers'" style="height:35px; border-top:2px solid #2c2c2c;">
      <v-btn text small title="Refresh Connections" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
      <v-btn text small title="New Connection" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <v-btn text small title="Remove Connection" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
    </div>
    <!-- OBJECTS -->
    <div v-else-if="treeviewMode == 'objects'" style="height:35px; border-top:2px solid #2c2c2c;">
      <v-btn :disabled="loading" @click="refreshObjects" text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="loading" text small title="New Database" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <v-btn :disabled="loading" text small title="Drop Database" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn v-if="database.length > 0" :disabled="loading || loadingServer" text small title="Import SQL" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-arrow-up</v-icon></v-btn>
      <v-btn v-if="database.length > 0" :disabled="loading || loadingServer" text small title="Export Objects" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-arrow-down</v-icon></v-btn>
      <span v-if="database.length > 0" :disabled="loading || loadingServer" style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn v-if="database.length > 0" :disabled="loading || loadingServer" text small title="Settings" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-cog</v-icon></v-btn>
    </div>
  </div>
</template>

<style scoped>
  ::v-deep .v-list-item__title {
  font-size: 0.9rem;
}
::v-deep .v-list-item__content {
  padding:0px;
}
::v-deep .v-list-item {
  min-height:40px;
}
</style>

<script>
import axios from 'axios'
import EventBus from '../js/event-bus'
import { mapFields } from '../js/map-fields'

export default {
  data() {
    return {
      loading: true,
      click: undefined,
      treeviewImg: {
        MySQL: "fas fa-server",
        PostgreSQL: "fas fa-server",
        Table: "fas fa-th",
        View: "fas fa-th-list",
        Trigger: "fas fa-bolt",
        Function: "fas fa-code-branch",
        Procedure: "fas fa-compress",
        Event: "far fa-clock"
      },
      treeviewColor: {
        MySQL: "#F29111",
        PostgreSQL: "",
        Table: "#ec644b",
        View: "#f2d984",
        Trigger: "#59abe3",
        Function: "#2abb9b",
        Procedure: "#bf55ec",
        Event: "#bdc3c7"
      },
    }
  },
  computed: {
    ...mapFields([
        'database',
        'databaseItems',
        'tableItems',
        'loadingServer',
        'treeviewItems',
        'treeview',
        'treeviewSearch',
        'treeviewMode',
        'treeviewOpened',
        'treeviewSelected',
        'server',
        'editorCompleters',
        'menuItems',
        'showMenu',
        'x',
        'y',
        'editor',
        'headerTab',
        'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  created() {
    this.getServers()
  },
  methods: {
    treeviewClick(item) {
      if (this.loadingServer) return
      return new Promise ((resolve) => {
        if (this.click) {
          clearTimeout(this.click)
          resolve('double')
        }
        this.click = setTimeout(() => {
          this.click = undefined          
          resolve('single')
        }, 200)
      }).then((data) => {
        // Single Click
        if (data == 'single') {
          if (item.children === undefined) {
            if (this.treeviewSelected == item) {
              this.treeviewSelected = {}
              this.headerTab = 0
              this.headerTabSelected = 'client'
              this.editor.focus()
            }
            else {
              this.treeviewSelected = item
              if (this.headerTabSelected == 'structure') EventBus.$emit('GET_STRUCTURE')
              else if (this.headerTabSelected == 'content') EventBus.$emit('GET_CONTENT')
              else if (this.headerTabSelected.startsWith('info_')) {
                let type = item.type.toLowerCase()
                this.headerTabSelected = 'info_' + type
                EventBus.$emit('GET_INFO', type)
              }
            }
          }
        }
        // Double Click
        else if (data == 'double') {
          this.treeview = [item]
          this.treeviewSelected = item
          if (this.treeviewMode == 'servers') this.getDatabases(item)
          else if (this.treeviewMode == 'objects') {
            if (['Table','View'].includes(item.type) && item.children === undefined) {
              this.treeview = []
              this.treeviewSelected = item
              this.headerTab = 2
              this.headerTabSelected = 'content'
              EventBus.$emit('GET_CONTENT')
            }
            else if (['Trigger','Function','Procedure','Event'].includes(item.type) && item.children === undefined) {
              let type = item.type.toLowerCase()
              this.headerTab = 3
              this.headerTabSelected = 'info_' + type
              EventBus.$emit('GET_INFO', type)
            }
          }
        }
      })
    },
    getServers() {
      this.loading = true
      axios.get('/client/servers')
        .then((response) => {
          this.parseServers(response.data.data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('SEND_NOTIFICATION', error.response.data.message, 'error')
        })
        .finally(() => { this.loading = false })
    },
    parseServers(data) {
      var servers = []
      for (let i = 0; i < data.length; ++i) {
        let found = false
        for (var j = 0; j < servers.length; ++j) {
          if (servers[j]['id'] == 'r' + data[i]['region_id']) {
            found = true
            break
          }
        }
        if (found) servers[j]['children'].push({ id: data[i]['server_id'], name: data[i]['server_name'], type: data[i]['server_engine'], host: data[i]['server_hostname'] })
        else servers.push({ id: 'r' + data[i]['region_id'], name: data[i]['region_name'], children: [{ id: data[i]['server_id'], name: data[i]['server_name'], type: data[i]['server_engine'], host: data[i]['server_hostname'] }] })
      }
      this.treeviewItems = servers.slice(0)
    },
    getDatabases(server) {
      this.loadingServer = true
      // Retrieve Databases
      axios.get('/client/databases', { params: { server_id: server.id } })
        .then((response) => {
          this.parseDatabases(server, response.data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('SEND_NOTIFICATION', error.response.data.message, 'error')
        })
        .finally(() => {
          this.loadingServer = false
        })
    },
    parseDatabases(server, data) {
      this.treeview = []
      this.treeviewItems = []
      this.treeviewSelected = {}
      this.treeviewMode = 'objects'
      this.server = server
      this.databaseItems = data.databases
      this.editor.focus()

      // Clean Treeview Search
      this.treeviewSearch = ''

      // Add database names to the editor autocompleter
      var completer = []
      for (let i = 0; i < data.length; ++i) completer.push({ value: data[i], meta: 'database' })
      this.editorAddCompleter(completer)

      // Get Column Types + Collations
      if (server.type == 'MySQL') {
        this.server.columnTypes = ['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT','FLOAT','DOUBLE','BIT','CHAR','VARCHAR','BINARY','VARBINARY','TINYBLOB','BLOB','MEDIUMBLOB','LONGBLOB','TINYTEXT','TEXT','MEDIUMTEXT','LONGTEXT','ENUM','SET','DATE','TIME','DATETIME','TIMESTAMP','YEAR','GEOMETRY','POINT','LINESTRING','POLYGON','GEOMETRYCOLLECTION','MULTILINESTRING','MULTIPOINT','MULTIPOLYGON','JSON']
        this.server.indexTypes = ['INDEX','UNIQUE','FULLTEXT']
        this.server.fkRules = ['Restrict','Cascade','Set NULL','No Action']
        this.server.collations = data.collations
      }
    },
    getObjects(database) {
      this.loading = true
      // Retrieve Tables
      axios.get('/client/objects', { params: { server_id: this.server.id, database_name: database } })
        .then((response) => {
          this.parseObjects(response.data)
          this.editor.focus()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('SEND_NOTIFICATION', error.response.data.message, 'error')
        })
        .finally(() => { this.loading = false })
    },
    parseObjects(data) {
      // Build routines
      var procedures = []
      var functions = []
      for (let i = 0; i < data.routines.length; ++i) {
        if (data.routines[i]['type'].toLowerCase() == 'procedure') procedures.push(data.routines[i])
        else functions.push(data.routines[i])
      }
      // Build tables / views
      var tables = []
      var views = []
      for (let i = 0; i < data.tables.length; ++i) {
        if (data.tables[i]['type'].toLowerCase() == 'table') tables.push(data.tables[i])
        else views.push(data.tables[i])
      }
      this.tableItems = tables.reduce((acc, val) => { acc.push(val['name']); return acc; }, [])

      // Build objects
      var objects = [
        { id: 'tables', 'name': 'Tables (' + tables.length + ')', type: 'Table', children: [] },
        { id: 'views', 'name': 'Views (' + views.length + ')',  type: 'View', children: [] },
        { id: 'triggers', 'name': 'Triggers (' + data.triggers.length + ')', type: 'Trigger', children: [] },
        { id: 'functions', 'name': 'Functions (' + functions.length + ')',  type: 'Function', children: [] },
        { id: 'procedures', 'name': 'Procedures (' + procedures.length + ')', type: 'Procedure', children: [] },
        { id: 'events', 'name': 'Events (' + data.events.length + ')',  type: 'Event', children: [] }
      ]
      // Parse Tables
      for (let i = 0; i < tables.length; ++i) {
        objects[0]['children'].push({ id: 'table|' + tables[i]['name'], ...tables[i], type: 'Table' })
      }
      // Parse Views
      for (let i = 0; i < views.length; ++i) {
        objects[1]['children'].push({ id: 'view|' + views[i]['name'], ...views[i], type: 'View' })
      }
      // Parse Triggers
      for (let i = 0; i < data.triggers.length; ++i) {
        objects[2]['children'].push({ id: 'trigger|' + data.triggers[i]['name'], ...data.triggers[i], type: 'Trigger' })
      }
      // Parse Functions
      for (let i = 0; i < functions.length; ++i) {
        objects[3]['children'].push({ id: 'function|' + functions[i]['name'], ...functions[i], type: 'Function' })
      }
      // Parse Procedures
      for (let i = 0; i < procedures.length; ++i) {
        objects[4]['children'].push({ id: 'procedure|' + procedures[i]['name'], ...procedures[i], type: 'Procedure' })
      }
      // Parse Events
      for (let i = 0; i < data.events.length; ++i) {
        objects[5]['children'].push({ id: 'event|' + data.events[i]['name'], ...data.events[i], type: 'Event' })
      }
      this.treeviewItems = objects

      // Add table / view names to the editor autocompleter
      var completer = []
      for (let i = 0; i < data.tables.length; ++i) completer.push({ value: data.tables[i]['name'], meta: data.tables[i]['type'] })
      for (let i = 0; i < data.columns.length; ++i) completer.push({ value: data.columns[i]['name'], meta: 'column' })
      if (this.editorCompleters.length > 1) this.editorRemoveCompleter(1)
      this.editorAddCompleter(completer)
    },
    editorAddCompleter(list) {
      const newCompleter = {
        identifierRegexps: [/[^\s]+/],
        getCompletions: function(editor, session, pos, prefix, callback) {
          callback(
            null,
            list.filter(entry => {
              return entry.value.toLowerCase().includes(prefix.toLowerCase())
            }).map(entry => {
              return { 
                value: entry.value,
                meta: entry.meta
              };
            })
          );
        }
      }
      this.editor.completers.push(newCompleter)
      this.editorCompleters.push(newCompleter)
    },
    editorRemoveCompleter(index) {
      this.editor.completers.splice(index+1, 1)
      this.editorCompleters.splice(index, 1)
    },
    clickAction(){
      alert('clicked');
    },
    showContextMenu(e) {
      e.preventDefault();
      this.showMenu = false;
      this.x = e.clientX;
      this.y = e.clientY;
      this.$nextTick(() => {
        this.showMenu = true;
      });
    },
    refreshObjects() {
      // promise
      this.getDatabases(this.server)
      if (this.database.length > 0) this.getObjects(this.database)
    },
  },
}
</script>