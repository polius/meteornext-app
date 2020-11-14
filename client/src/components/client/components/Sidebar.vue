<template>
  <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
    <div style="height:calc(100% - 36px)">
      <v-autocomplete ref="database" v-model="database" :disabled="sidebarLoading || databaseItems.length == 0" @change="databaseChanged" solo :items="databaseItems" label="Database" auto-select-first hide-details background-color="#303030" height="48px" style="padding:10px;"></v-autocomplete>
      <div v-if="sidebarMode == 'servers' || database.length != 0" class="subtitle-2" style="padding-left:10px; padding-top:8px; padding-bottom:8px; color:rgb(222,222,222);">{{ (sidebarMode == 'servers') ? 'SERVERS' : 'OBJECTS' }}<v-progress-circular v-if="sidebarLoading" indeterminate size="15" width="2" style="margin-left:15px;"></v-progress-circular></div>
      <div v-else-if="database.length == 0" class="body-2" style="padding-left:20px; padding-top:10px; padding-bottom:7px; color:rgb(222,222,222);"><v-icon small style="padding-right:10px; padding-bottom:4px;">fas fa-arrow-up</v-icon>Select a database</div>
      <div v-if="sidebarMode == 'servers' || database.length > 0" style="height:100%">
        <v-treeview :active.sync="sidebarSelected" item-key="id" :open.sync="sidebarOpened" :items="sidebarItems" :search="sidebarSearch" activatable multiple-active open-on-click transition return-object class="clear_shadow" style="height:calc(100% - 162px); width:100%; overflow-y:auto;">
          <template v-slot:label="{item, open}">
            <v-btn text @click="sidebarClicked($event, item)" @contextmenu="showContextMenu($event, item)" style="font-size:14px; text-transform:none; font-weight:400; width:100%; justify-content:left; padding:0px;"> 
              <v-icon v-if="'children' in item" small style="padding:10px;">
                {{ open ? 'mdi-folder-open' : 'mdi-folder' }}
              </v-icon>
              <v-icon v-else small :title="item.version" :color="sidebarColor[item.engine]" style="padding:10px;">
                {{ sidebarImg[item.engine] }}
              </v-icon>
              {{item.name}}
              <v-spacer></v-spacer>
              <v-progress-circular v-if="loadingServer && sidebarMode == 'servers' && ((sidebarSelected.length > 0 && item.id == sidebarSelected[0].id) || item.id == contextMenuItem.id)" indeterminate size="16" width="2" color="white" style="margin-right:10px;"></v-progress-circular>
              <!-- <v-chip label outlined small style="margin-left:10px; margin-right:10px;">Prod</v-chip> -->
            </v-btn>
          </template>
        </v-treeview>
        <v-menu v-model="contextMenu" :position-x="contextMenuX" :position-y="contextMenuY" absolute offset-y style="z-index:10">
          <v-list style="padding:0px;">
            <v-list-item-group v-model="contextMenuModel">
              <div v-for="[index, item] of contextMenuItems.entries()" :key="index">
                <v-list-item :disabled="sidebarSelected.length > 1 && !item.m" v-if="item.i != '|'" @click="contextMenuClicked(item.i)">
                  <v-list-item-title>{{ sidebarSelected.length > 1 && item.s ? item.i + 's' : item.i }}</v-list-item-title>
                </v-list-item>
                <v-divider v-else></v-divider>
              </div>
            </v-list-item-group>
          </v-list>
        </v-menu>
        <v-text-field v-if="sidebarItems.length > 0" :disabled="sidebarMode == 'objects' && database.length == 0" v-model="sidebarSearch" label="Search" dense solo hide-details height="38px" style="float:left; width:100%; padding:10px;"></v-text-field>
      </div>
    </div>
    <!---------------------------->
    <!-- CONTEXT MENU - DIALOGs -->
    <!---------------------------->
    <Tables :contextMenuItem="contextMenuItem" />
    <Views :contextMenuItem="contextMenuItem" />
    <Triggers :contextMenuItem="contextMenuItem" />
    <Procedures :contextMenuItem="contextMenuItem" />
    <Functions :contextMenuItem="contextMenuItem" />
    <Events :contextMenuItem="contextMenuItem" />
    <!--------------------->
    <!-- LEFT BOTTOM BAR -->
    <!--------------------->
    <BottomBar />
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" persistent max-width="50%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">Unable to apply changes</div>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogText }}</div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn @click="dialog = false" color="primary">Close</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
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

import Tables from './sidebar/Tables'
import Views from './sidebar/Views'
import Triggers from './sidebar/Triggers'
import Procedures from './sidebar/Procedures'
import Functions from './sidebar/Functions'
import Events from './sidebar/Events'

import BottomBar from './BottomBar'

export default {
  data() {
    return {
      // Loading
      loadingServer: false,

      // Sidebar
      sidebarClick: undefined,
      sidebarImg: {
        MySQL: "fas fa-server",
        "Aurora MySQL": "fas fa-server",
        PostgreSQL: "fas fa-server",
        Table: "fas fa-th",
        View: "fas fa-th-list",
        Trigger: "fas fa-bolt",
        Function: "fas fa-code-branch",
        Procedure: "fas fa-compress",
        Event: "far fa-clock"
      },
      sidebarColor: {
        MySQL: "#F29111",
        "Aurora MySQL": "#F29111",
        PostgreSQL: "",
        Table: "#ec644b",
        View: "#f2d984",
        Trigger: "#59abe3",
        Function: "#2abb9b",
        Procedure: "#bf55ec",
        Event: "#bdc3c7"
      },
      // Sidebar - Context Menu
      contextMenu: false,
      contextMenuModel: null,
      contextMenuItems: [],
      contextMenuItem: {},
      contextMenuX: 0,
      contextMenuY: 0,
      // Dialog
      dialog: false,
      dialogText: '',
    }
  },
  components: { Tables, Views, Triggers, Procedures, Functions, Events, BottomBar },
  computed: {
    ...mapFields([
      'servers',
    ], { path: 'client/client' }),
    ...mapFields([
      'editor',
      'editorCompleters',
      'gridApi',
    ], { path: 'client/components' }),
    ...mapFields([
      'index',
      'database',
      'databaseItems',
      'tableItems',
      'sidebarItems',
      'sidebarSearch',
      'sidebarMode',
      'sidebarOpened',
      'sidebarSelected',
      'sidebarLoading',
      'server',
      'headerTab',
      'headerTabSelected',
      'objectsTab',
      'tabObjectsSelected',
      'objectsHeaders',
    ], { path: 'client/connection' }),
  },
  created() {
    this.getServers()
  },
  mounted() {
    EventBus.$on('execute-sidebar', this.execute);
    EventBus.$on('get-sidebar-servers', this.getServers);
    EventBus.$on('get-sidebar-objects', this.getObjects);
    EventBus.$on('refresh-sidebar-objects', this.refreshObjects);
  },
  methods: {
    sidebarClicked(event, item) {
      if (this.loadingServer) return
      this.clickHandler(event, item)
      return new Promise ((resolve) => {
        if (this.sidebarClick) {
          clearTimeout(this.sidebarClick)
          resolve('double')
        }
        this.sidebarClick = setTimeout(() => {
          this.sidebarClick = undefined
          resolve('single')
        }, 200)
      }).then((data) => {
        setTimeout(() => {
          // Single Click
          if (data == 'single' && item.children === undefined) {
            if (this.sidebarSelected.length > 1) {
              this.headerTab = 0
              this.headerTabSelected = 'client'
              this.editor.focus()
            }
            else {
              if (this.headerTabSelected == 'structure') EventBus.$emit('get-structure')
              else if (this.headerTabSelected == 'content') EventBus.$emit('get-content')
              else if (this.headerTabSelected.startsWith('info_')) {
                let type = item.type.toLowerCase()
                this.headerTabSelected = 'info_' + type
                EventBus.$emit('get-info', type)
              }
            }
          }
          // Double Click
          else if (data == 'double' && item.children === undefined) {
            if (this.sidebarMode == 'servers') this.getDatabases(item)
            else if (this.sidebarMode == 'objects') {
              if (['Table','View'].includes(item.type) && item.children === undefined) {
                this.headerTab = 2
                this.headerTabSelected = 'content'
                EventBus.$emit('get-content')
              }
              else if (['Trigger','Function','Procedure','Event'].includes(item.type) && item.children === undefined) {
                let type = item.type.toLowerCase()
                this.headerTab = 3
                this.headerTabSelected = 'info_' + type
                EventBus.$emit('get-info', type)
              }
            }
          }
        }, 10)
      })
    },
    clickHandler(event, item) {
      const lastElement = this.sidebarSelected.length == 0 ? undefined : this.sidebarSelected[this.sidebarSelected.length - 1]
      if ('children' in item) {
        if (item.children.length == 0) this.sidebarSelected = []
      }
      else if (event.ctrlKey || event.metaKey ) {
        if (lastElement !== undefined && lastElement.parentId != item.parentId) this.sidebarSelected = [] 
      }
      else if (event.shiftKey) {
        // Find last index
        let lastParentIndex = -1
        let lastIndex = -1
        if (this.sidebarSelected.length != 0) {
          lastParentIndex = this.sidebarItems.findIndex(x => x.id == lastElement.parentId)
          lastIndex = this.sidebarItems[lastParentIndex]['children'].findIndex(x => x.id == lastElement.id)
        }
        // Find new index
        let newParentIndex = this.sidebarItems.findIndex(x => x.id == item.parentId)
        let newIndex = this.sidebarItems[newParentIndex]['children'].findIndex(x => x.id == item.id)
        setTimeout(() => {
          this.sidebarSelected = []
          // Select all rows from 0 to selected
          if (lastIndex == -1) {
            for (let i = 0; i <= newIndex; ++i) this.sidebarSelected.push(this.sidebarItems[newParentIndex]['children'][i])
          }
          // Select rows between
          else if (lastParentIndex == newParentIndex) {
            if (lastIndex < newIndex) for (let i = lastIndex; i <= newIndex; ++i) this.sidebarSelected.push(this.sidebarItems[newParentIndex]['children'][i])
            else for (let i = lastIndex; i >= newIndex; --i) this.sidebarSelected.push(this.sidebarItems[newParentIndex]['children'][i])
          }
          // Select selected row
          else this.sidebarSelected.push(this.sidebarItems[newParentIndex]['children'][newIndex])
        }, 10)
      }
      else this.sidebarSelected = []
    },
    getServers() {
      this.sidebarLoading = true
      axios.get('/client/servers')
        .then((response) => {
          this.parseServers(response.data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message, 'error')
        })
        .finally(() => { this.sidebarLoading = false })
    },
    parseServers(data) {
      var servers = []
      // Parse Server Folders
      for (let folder of data.folders) {
        folder['id'] = 'f' + folder['id']
        folder['children'] = []
        servers.push(folder)
      }
      // Parse Servers
      for (let server of data.servers) {
        if (server.folder_id == null) servers.push(server)
        else {
          const index = servers.findIndex(x => 'children' in x && server.folder_id == x.id.substring(1))
          servers[index]['children'].push(server)
        }
      }
      this.servers = servers.slice(0)
      this.sidebarItems = servers.slice(0)
    },
    getDatabases(server) {
      this.loadingServer = true
      // Retrieve Databases
      const payload = {
        connection: this.index,
        server: server.id,
      }
      axios.get('/client/databases', { params: payload })
        .then((response) => {
          this.parseDatabases(server, response.data)
        })
        .catch((error) => {
          if (error.response.status == 401) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message, 'error')
        })
        .finally(() => {
          this.loadingServer = false
        })
    },
    parseDatabases(server, data) {
      // Assign server
      this.server = server

      // Init sidebar
      this.sidebarMode = 'objects'
      this.sidebarSearch = ''

      // Build Databases
      this.databaseItems = []
      var completer = []
      for (let i = 0; i < data.databases.length; ++i) {
        this.databaseItems.push({ text: data.databases[i]['name'], encoding: data.databases[i]['encoding'], collation: data.databases[i]['collation'] })
        completer.push({ value: data.databases[i]['name'], meta: 'Database' })
      }

      // Add database names to the editor autocompleter
      this.editorAddCompleter(completer)

      // Get Column Types + Collations
      if (server.type == 'MySQL') {
        this.server.version = data.version
        this.server.engines = data.engines
        this.server.encodings = data.encodings
        this.server.defaults = data.defaults
        this.server.columnTypes = ['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT','FLOAT','DOUBLE','BIT','CHAR','VARCHAR','BINARY','VARBINARY','TINYBLOB','BLOB','MEDIUMBLOB','LONGBLOB','TINYTEXT','TEXT','MEDIUMTEXT','LONGTEXT','ENUM','SET','DATE','TIME','DATETIME','TIMESTAMP','YEAR','GEOMETRY','POINT','LINESTRING','POLYGON','GEOMETRYCOLLECTION','MULTILINESTRING','MULTIPOINT','MULTIPOLYGON','JSON']
        this.server.indexTypes = ['PRIMARY','INDEX','UNIQUE','FULLTEXT']
        this.server.fkRules = ['Restrict','Cascade','Set NULL','No Action']
      }

      // Focus database
      this.$nextTick(() => { this.$refs.database.focus() })
    },
    databaseChanged(database) {
      if (database === undefined) return
      // Clear Sidebar
      this.sidebarSelected = []
      this.sidebarOpened = []
      this.sidebarItems = []
      // Clear Tab
      this.headerTab = 0
      this.headerTabSelected = 'client'
      // Get Objects
      new Promise((resolve, reject) => { 
        this.getObjects(database, resolve, reject)
      }).finally(() => { this.editor.focus() })
    },
    getObjects(database, resolve, reject) {
      this.sidebarLoading = true
      // Retrieve Tables
      const payload = {
        connection: this.index,
        server: this.server.id,
        database: database
      }
      axios.get('/client/objects', { params: payload })
        .then((response) => {
          this.parseObjects(response.data)
          resolve()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message, 'error')
          reject(error)
        })
        .finally(() => { this.sidebarLoading = false })
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
      var completer = []
      var objects = [
        { id: 'tables', 'name': 'Tables (' + tables.length + ')', type: 'Table', children: [] },
        { id: 'views', 'name': 'Views (' + views.length + ')',  type: 'View', children: [] },
        { id: 'triggers', 'name': 'Triggers (' + data.triggers.length + ')', type: 'Trigger', children: [] },
        { id: 'functions', 'name': 'Functions (' + functions.length + ')',  type: 'Function', children: [] },
        { id: 'procedures', 'name': 'Procedures (' + procedures.length + ')', type: 'Procedure', children: [] },
        { id: 'events', 'name': 'Events (' + data.events.length + ')',  type: 'Event', children: [] }
      ]
      // Parse Columns
      for (let i = 0; i < data.columns.length; ++i) {
        completer.push({ value: data.columns[i]['name'], meta: 'Column: ' + data.columns[i]['type'] })
      }
      // Parse Tables
      for (let i = 0; i < tables.length; ++i) {
        objects[0]['children'].push({ id: 'table|' + tables[i]['name'], ...tables[i], type: 'Table', parentId: 'tables' })
        completer.push({ value: tables[i]['name'], meta: 'Table' })
      }
      // Parse Views
      for (let i = 0; i < views.length; ++i) {
        objects[1]['children'].push({ id: 'view|' + views[i]['name'], ...views[i], type: 'View', parentId: 'views' })
        completer.push({ value: views[i]['name'], meta: 'View' })
      }
      // Parse Triggers
      for (let i = 0; i < data.triggers.length; ++i) {
        objects[2]['children'].push({ id: 'trigger|' + data.triggers[i]['name'], ...data.triggers[i], type: 'Trigger', parentId: 'triggers' })
        completer.push({ value: data.triggers[i]['name'], meta: 'Trigger' })
      }
      // Parse Functions
      for (let i = 0; i < functions.length; ++i) {
        objects[3]['children'].push({ id: 'function|' + functions[i]['name'], ...functions[i], type: 'Function', parentId: 'functions' })
        completer.push({ value: functions[i]['name'], meta: 'Function' })
      }
      // Parse Procedures
      for (let i = 0; i < procedures.length; ++i) {
        objects[4]['children'].push({ id: 'procedure|' + procedures[i]['name'], ...procedures[i], type: 'Procedure', parentId: 'procedures' })
        completer.push({ value: procedures[i]['name'], meta: 'Procedure' })
      }
      // Parse Events
      for (let i = 0; i < data.events.length; ++i) {
        objects[5]['children'].push({ id: 'event|' + data.events[i]['name'], ...data.events[i], type: 'Event', parentId: 'events' })
        completer.push({ value: data.events[i]['name'], meta: 'Event' })
      }
      this.sidebarItems = objects

      // Add objects to the editor autocompleter
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

      // // Calculate autocomplete width
      // let width = Math.max(...(list.map(el => el.value.length + el.meta.length)))
      // this.editor.completer.popup.container.style.width='min(35vw, ' + (width*9+50) + 'px)'
    },
    editorRemoveCompleter(index) {
      this.editor.completers.splice(index+1, 1)
      this.editorCompleters.splice(index, 1)
    },
    refreshObjects(resolve, reject) {
      this.getDatabases(this.server)
      if (this.database.length > 0) {
        this.getObjects(this.database, resolve, reject)
      }
    },
    showContextMenu(e, item) {
      e.preventDefault()
      this.contextMenuModel = null
      this.contextMenuX = e.clientX
      this.contextMenuY = e.clientY
      const found = this.sidebarSelected.find((x) => x.id == item.id)
      if (!found) this.sidebarSelected = [item]
      this.buildContextMenu(item)
    },
    buildContextMenu(item) {
      this.contextMenuItem = item
      this.contextMenuItems = []
      const m = true, s = true
      if (this.sidebarMode == 'servers') {
        if (item.children === undefined) this.contextMenuItems = [{i:'Open Connection'}, {i:'Test Connection'}, {i:'|'}, {i:'New Server',m}, {i:'Move Server',m,s}, {i:'Remove Server',m,s}]
        else this.contextMenuItems = [{i:'New Server'}, {i:'|'}, {i:'New Folder'}, {i:'Rename Folder'}, {i:'Remove Folder'}]
      }
      else if (this.sidebarMode == 'objects') {
        if (item.type == 'Table') {
          if (item.children === undefined) this.contextMenuItems = [{i:'Create Table',m}, {i:'|'}, {i:'Rename Table'}, {i:'Duplicate Table'}, {i:'|'}, {i:'Truncate Table',m,s}, {i:'Delete Table',m,s}, {i:'|'}, {i:'Export',m}, {i:'|'}, {i:'Copy Table Syntax'}]
          else this.contextMenuItems = [{i:'Create Table'}, {i:'|'}, {i:'Show Table Objects'}]
        }
        else if (item.type == 'View') {
          if (item.children === undefined) this.contextMenuItems = [{i:'Create View',m}, {i:'|'}, {i:'Rename View'}, {i:'Duplicate View'}, {i:'|'}, {i:'Delete View',m,s}, {i:'|'}, {i:'Export',m}, {i:'|'}, {i:'Copy View Syntax'}]
          else this.contextMenuItems = [{i:'Create View'}, {i:'|'}, {i:'Show View Objects'}]
        }
        else if (item.type == 'Trigger') {
          if (item.children === undefined) this.contextMenuItems = [{i:'Create Trigger',m}, {i:'|'}, {i:'Rename Trigger'}, {i:'Duplicate Trigger'}, {i:'|'}, {i:'Delete Trigger',m,s}, {i:'|'}, {i:'Export',m}, {i:'|'}, {i:'Copy Trigger Syntax'}]
          else this.contextMenuItems = [{i:'Create Trigger'}, {i:'|'}, {i:'Show Trigger Objects'}]
        }
        else if (item.type == 'Function') {
          if (item.children === undefined) this.contextMenuItems = [{i:'Create Function',m}, {i:'|'}, {i:'Rename Function'}, {i:'Duplicate Function'}, {i:'|'}, {i:'Delete Function',m,s}, {i:'|'}, {i:'Export',m}, {i:'|'}, {i:'Copy Function Syntax'}]
          else this.contextMenuItems = [{i:'Create Function'}, {i:'|'}, {i:'Show Function Objects'}]
        }
        else if (item.type == 'Procedure') {
          if (item.children === undefined) this.contextMenuItems = [{i:'Create Procedure',m}, {i:'|'}, {i:'Rename Procedure'}, {i:'Duplicate Procedure'}, {i:'|'}, {i:'Delete Procedure',m,s}, {i:'|'}, {i:'Export',m}, {i:'|'}, {i:'Copy Procedure Syntax'}]
          else this.contextMenuItems = [{i:'Create Procedure'}, {i:'|'}, {i:'Show Procedure Objects'}]
        }
        else if (item.type == 'Event') {
          if (item.children === undefined) this.contextMenuItems = [{i:'Create Event',m}, {i:'|'}, {i:'Rename Event'}, {i:'Duplicate Event'}, {i:'|'}, {i:'Delete Event',m,s}, {i:'|'}, {i:'Export',m}, {i:'|'}, {i:'Copy Event Syntax'}]
          else this.contextMenuItems = [{i:'Create Event'}, {i:'|'}, {i:'Show Event Objects'}]
        }
      }
      this.contextMenu = true
    },
    contextMenuClicked(item) {
      if (this.sidebarMode == 'servers') {
        if (item == 'Open Connection') this.getDatabases(this.contextMenuItem)
        else if (item == 'Test Connection') 1 == 1
        else if (item == 'New Server') EventBus.$emit('show-bottombar-servers-new')
        else if (item == 'Move Server') EventBus.$emit('show-bottombar-servers-move')
        else if (item == 'Remove Server') EventBus.$emit('show-bottombar-servers-remove')
        else if (item == 'New Folder') EventBus.$emit('show-bottombar-servers-new-folder')
        else if (item == 'Rename Folder') EventBus.$emit('show-bottombar-servers-rename-folder')
        else if (item == 'Remove Folder') EventBus.$emit('show-bottombar-servers-remove-folder')
      }
      else if (this.sidebarMode == 'objects') {
        if (this.contextMenuItem.type == 'Table') {
          if (item == 'Show Table Objects') this.showObjectsTab('tables')
          else EventBus.$emit('click-contextmenu-table', item)
        }
        else if (this.contextMenuItem.type == 'View') {
          if (item == 'Show View Objects') this.showObjectsTab('views')
          else EventBus.$emit('click-contextmenu-view', item)
        }
        else if (this.contextMenuItem.type == 'Trigger') {
          if (item == 'Show Trigger Objects') this.showObjectsTab('triggers')
          else EventBus.$emit('click-contextmenu-trigger', item)
        }
        else if (this.contextMenuItem.type == 'Function') {
          if (item == 'Show Function Objects') this.showObjectsTab('functions')
          else EventBus.$emit('click-contextmenu-function', item)
        }
        else if (this.contextMenuItem.type == 'Procedure') {
          if (item == 'Show Procedure Objects') this.showObjectsTab('procedures')
          else EventBus.$emit('click-contextmenu-procedure', item)
        }
        else if (this.contextMenuItem.type == 'Event') {
          if (item == 'Show Event Objects') this.showObjectsTab('events')
          else EventBus.$emit('click-contextmenu-event', item)
        }
      }
    },
    showObjectsTab(object) {
      this.headerTab = 6
      this.headerTabSelected = 'objects'
      this.objectsTab = (object == 'tables') ? 1 : (object == 'views') ? 2 : (object == 'triggers') ? 3 : (object == 'functions') ? 4 : (object == 'procedures') ? 5 : (object == 'events') ? 6 : 0
      this.tabObjectsSelected = object
      if (this.objectsHeaders[object].length == 0) {
        setTimeout(() => {
          let promise = new Promise((resolve, reject) => {
            this.gridApi.objects[object].showLoadingOverlay()
            EventBus.$emit('get-objects', resolve, reject)
          })
          promise.then(() => {})
            .catch(() => {})
            .finally(() => { this.gridApi.objects.events.hideOverlay() })
        }, 500)
      }
    },
    execute(queries, resolve, reject) {
      // Execute Query
      const payload = {
        connection: this.index,
        server: this.server.id,
        database: this.database,
        queries: queries
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          resolve(response.data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            let data = JSON.parse(error.response.data.data)
            // Show error
            this.dialogText = data[0]['error']
            this.dialog = true
            // Reject promise
            reject()
          }
        })
    },
  }
}
</script>