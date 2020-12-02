<template>
  <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
    <div style="height:calc(100% - 36px)">
      <v-autocomplete v-if="sidebarMode == 'servers'" ref="server" v-model="serverSearch" :loading="loadingServer" :disabled="loadingServer" @change="serverChanged" solo :items="serversList" item-text="name" label="Search" auto-select-first hide-details return-object background-color="#303030" height="48px" style="padding:10px;">
        <template v-slot:[`selection`]="{ item }">
          <div class="body-2">
            <v-icon small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? 'error' : 'warning'" style="margin-right:10px">fas fa-server</v-icon>
            <span class="body-2">{{ item.name }}</span>
            <span v-show="item.folder != null" class="body-2" style="font-weight:300; margin-left:8px;">{{ '(' + item.folder + ')' }}</span>
          </div>
        </template>
        <template v-slot:[`item`]="{ item }">
          <div class="body-2">
            <v-icon small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? 'error' : 'warning'" style="margin-right:10px">fas fa-server</v-icon>
            <span class="body-2">{{ item.name }}</span>
            <span v-show="item.folder != null" class="body-2" style="font-weight:300; margin-left:8px;">{{ '(' + item.folder + ')' }}</span>
          </div>
        </template>
      </v-autocomplete>
      <v-autocomplete v-else ref="database" v-model="database" :disabled="sidebarLoading || databaseItems.length == 0" @change="databaseChanged" solo :items="databaseItems" label="Database" auto-select-first hide-details background-color="#303030" height="48px" style="padding:10px;"></v-autocomplete>
      <div v-if="sidebarMode == 'servers' || database.length != 0" class="subtitle-2" style="padding-left:10px; padding-top:8px; padding-bottom:8px; color:rgb(222,222,222);">{{ (sidebarMode == 'servers') ? 'SERVERS' : 'OBJECTS' }}<v-progress-circular v-if="sidebarLoading" indeterminate size="15" width="2" style="margin-left:15px;"></v-progress-circular></div>
      <div v-else-if="database.length == 0" class="body-2" style="padding-left:20px; padding-top:10px; padding-bottom:7px; color:rgb(222,222,222);"><v-icon small style="padding-right:10px; padding-bottom:4px;">fas fa-arrow-up</v-icon>Select a database</div>
      <div v-if="sidebarMode == 'servers' || database.length > 0" style="height:100%">
        <v-treeview :active.sync="sidebarSelected" item-key="id" :open.sync="sidebarOpened" :items="sidebarItems" :search="sidebarSearch" activatable multiple-active open-on-click transition return-object class="clear_shadow" :style="`${sidebarMode == 'servers' ? `height:calc(100% - 107px)` : `height:calc(100% - 162px)`}; width:100%; overflow-y:auto;`">
          <template v-slot:label="{item, open}">
            <v-btn text @click="sidebarClicked($event, item)" @contextmenu="showContextMenu($event, item)" style="font-size:14px; text-transform:none; font-weight:400; width:100%; justify-content:left; padding:0px;"> 
              <v-icon v-if="'children' in item && sidebarMode == 'servers'" small style="padding:10px;">{{ open ? 'mdi-folder-open' : 'mdi-folder' }}</v-icon>
              <v-icon v-else-if="sidebarMode == 'servers'" small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? 'error' : 'warning'" style="padding:10px;">fas fa-server</v-icon>
              <v-icon v-else small :title="item.type" :color="sidebarColor[item.type]" style="padding:10px;">{{ sidebarImg[item.type] }}</v-icon>
              {{ item.name }}
              <v-spacer></v-spacer>
              <v-progress-circular v-if="loadingServer && sidebarMode == 'servers' && sidebarSelected.length == 1 && item.id == sidebarSelected[0].id" indeterminate size="16" width="2" color="white" style="margin-right:10px;"></v-progress-circular>
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
        <v-text-field v-if="sidebarMode == 'objects' && sidebarItems.length > 0" :disabled="sidebarMode == 'objects' && database.length == 0" v-model="sidebarSearch" label="Search" dense solo hide-details height="38px" style="float:left; width:100%; padding:10px;"></v-text-field>
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
              <div class="text-h6" style="font-weight:400;">{{ dialogTitle }}</div>
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
      // Server search
      serverSearch: {},

      // Loading
      loadingServer: false,

      // Sidebar
      sidebarClick: undefined,
      sidebarImg: {
        Table: "fas fa-th",
        View: "fas fa-th-list",
        Trigger: "fas fa-bolt",
        Function: "fas fa-code-branch",
        Procedure: "fas fa-compress",
        Event: "far fa-clock"
      },
      sidebarColor: {
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
      dialogTitle: '',
      dialogText: '',
    }
  },
  components: { Tables, Views, Triggers, Procedures, Functions, Events, BottomBar },
  computed: {
    ...mapFields([
      'servers',
      'serversList',
      'dialogOpened',
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
    new Promise((resolve, reject) => this.getServers(resolve, reject))
  },
  mounted() {
    EventBus.$on('execute-sidebar', this.execute);
    EventBus.$on('get-sidebar-servers', this.getServers);
    EventBus.$on('get-sidebar-objects', this.getObjects);
    EventBus.$on('refresh-sidebar-objects', this.refreshObjects);
    this.$refs.server.focus()
  },
  watch: {
    dialog: function(val) {
      this.dialogOpened = val
      if (!val) {
        this.serverSearch = {}
        setTimeout(() => this.$refs.server.focus(),100)
      }
    },
    sidebarMode: function(val) {
      if (val == 'servers') {
        this.serverSearch = {}
        setTimeout(() => this.$refs.server.focus(),100)
      }
    }
  },
  methods: {
    serverChanged(val) {
      if (val === undefined || val.length == 0) return
      const server = this.findServer(val.id)
      this.sidebarSelected = [server]
      this.getDatabases(server)
    },
    findServer(id) {
      for (let i of this.servers) {
        if ('children' in i) {
          for (let j of i['children']) {
            if (j.id == id) return j
          }
        }
        else if (i.id == id) return i
      }
    },
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
              else if (this.headerTabSelected == 'content') EventBus.$emit('get-content', true)
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
                EventBus.$emit('get-content', true)
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
          if (lastParentIndex == -1) lastIndex = this.sidebarItems.findIndex(x => x.id == lastElement.id)
          else lastIndex = this.sidebarItems[lastParentIndex]['children'].findIndex(x => x.id == lastElement.id)
        }
        // Find new index
        let newParentIndex = this.sidebarItems.findIndex(x => x.id == item.parentId)
        let newIndex = -1
        if (newParentIndex == -1) newIndex = this.sidebarItems.findIndex(x => x.id == item.id)
        else newIndex = this.sidebarItems[newParentIndex]['children'].findIndex(x => x.id == item.id)
        
        setTimeout(() => {
          this.sidebarSelected = []
          // Select all rows from 0 to selected
          if (lastIndex == -1) {
            if (newParentIndex == -1) {
              for (let i = 0; i <= newIndex; ++i) if (!('children' in this.sidebarItems[i])) this.sidebarSelected.push(this.sidebarItems[i])
            }
            else for (let i = 0; i <= newIndex; ++i) this.sidebarSelected.push(this.sidebarItems[newParentIndex]['children'][i])
          }
          // Select rows between
          else if (lastParentIndex == newParentIndex) {
            if (lastParentIndex == -1) {
              if (lastIndex < newIndex) for (let i = lastIndex; i <= newIndex; ++i) this.sidebarSelected.push(this.sidebarItems[i])
              else for (let i = lastIndex; i >= newIndex; --i) this.sidebarSelected.push(this.sidebarItems[i])
            }
            else {
              if (lastIndex < newIndex) for (let i = lastIndex; i <= newIndex; ++i) this.sidebarSelected.push(this.sidebarItems[newParentIndex]['children'][i])
              else for (let i = lastIndex; i >= newIndex; --i) this.sidebarSelected.push(this.sidebarItems[newParentIndex]['children'][i])
            }
          }
          // Select selected row
          else {
            if (newParentIndex == -1) this.sidebarSelected.push(this.sidebarItems[newIndex])
            else this.sidebarSelected.push(this.sidebarItems[newParentIndex]['children'][newIndex])
          }
        }, 10)
      }
      else this.sidebarSelected = []
    },
    getServers(resolve, reject) {
      this.sidebarLoading = true
      axios.get('/client/servers')
        .then((response) => {
          this.parseServers(response.data)
          resolve()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message, 'error')
          reject()
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
          server['parentId'] = servers[index].id
          servers[index]['children'].push(server)
        }
      }
      this.servers = servers.slice(0)
      this.sidebarItems = servers.slice(0)
      // Parse Servers List
      this.serversList = data.servers.map(x => ({ id: x.id, name: x.name, shared: x.shared, folder: x.folder_name }))
    },
    getDatabases(server) {
      this.loadingServer = true
      // Retrieve Databases
      const payload = {
        connection: 0,
        server: server.id,
      }
      axios.get('/client/databases', { params: payload })
        .then((response) => {
          this.parseDatabases(server, response.data)
        })
        .catch((error) => {
          if (error.response.status == 401) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            this.dialogTitle = "Can't connect to the server"
            this.dialogText = error.response.data.message
            this.dialog = true
          }
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

      new Promise(() => {
        // Build Databases
        this.databaseItems = data.databases
        // const arr = Array.from({length: 10000}, () => Math.floor(Math.random() * 10000))
        // this.databaseItems = arr

        // Add database names to the editor autocompleter
        let completer = data.databases.reduce((acc, val) => {
          acc.push({value: val.toString(), meta: 'Database'})
          return acc
        },[])
        this.editorAddCompleter(completer)
      })

      // Get Column Types + Collations
      if (['MySQL','Aurora MySQL'].includes(server.engine)) {
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
        connection: 0,
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
      for (let routine of data.routines) {
        if (routine['type'].toLowerCase() == 'procedure') procedures.push(routine)
        else functions.push(routine)
      }
      // Build tables / views
      var tables = []
      var views = []
      for (let table of data.tables) {
        if (table['type'].toLowerCase() == 'table') tables.push(table)
        else views.push(table)
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
      for (let column of data.columns) {
        completer.push({ value: column['name'], meta: 'Column: ' + column['type'] })
      }
      // Parse Tables
      for (let table of tables) {
        objects[0]['children'].push({ id: 'table|' + table['name'], ...table, type: 'Table', parentId: 'tables' })
        completer.push({ value: table['name'], meta: 'Table' })
      }
      // Parse Views
      for (let view of views) {
        objects[1]['children'].push({ id: 'view|' + view['name'], ...view, type: 'View', parentId: 'views' })
        completer.push({ value: view['name'], meta: 'View' })
      }
      // Parse Triggers
      for (let trigger of data.triggers) {
        objects[2]['children'].push({ id: 'trigger|' + trigger, name: trigger, type: 'Trigger', parentId: 'triggers' })
        completer.push({ value: trigger, meta: 'Trigger' })
      }

      // Parse Functions
      for (let f of functions) {
        objects[3]['children'].push({ id: 'function|' + f['name'], ...f, type: 'Function', parentId: 'functions' })
        completer.push({ value: f['name'], meta: 'Function' })
      }
      // Parse Procedures
      for (let procedure of procedures) {
        objects[4]['children'].push({ id: 'procedure|' + procedure['name'], ...procedure, type: 'Procedure', parentId: 'procedures' })
        completer.push({ value: procedure['name'], meta: 'Procedure' })
      }
      // Parse Events
      for (let event of data.events) {
        objects[5]['children'].push({ id: 'event|' + event['name'], ...event, type: 'Event', parentId: 'events' })
        completer.push({ value: event['name'], meta: 'Event' })
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
        else if (item == 'Test Connection') this.testConnection()
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
        connection: 0,
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
            this.dialogTitle = 'Unable to apply changes'
            this.dialogText = data[0]['error']
            this.dialog = true
            // Reject promise
            reject()
          }
        })
    },
    testConnection() {
      // Test Connection
      EventBus.$emit('send-notification', 'Testing Server...', 'info', true)
      this.loading = true
      const payload = {
        region: this.contextMenuItem.region_id,
        server: this.contextMenuItem.id,
      }
      axios.post('/inventory/servers/test', payload)
        .then((response) => {
          EventBus.$emit('send-notification', response.data.message, '#00b16a', 2)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            this.dialogTitle = "Can't connect to the server"
            EventBus.$emit('send-notification', this.dialogTitle, 'error', 2)
            this.dialogText = error.response.data.message
            this.dialog = true
          }
        })
        .finally(() => { this.loading = false })
    },
  }
}
</script>