<template>
  <div>
    <v-row no-gutters>
      <v-col class="flex-grow-1 flex-shrink-1">
        <v-tabs v-model="currentConn" @contextmenu.native="onContextMenu" v-if="Object.keys(server).length != 0 || connections.length > 1" hide-slider show-arrows dense background-color="#2c2c2c" color="white" slider-color="#969696" slider-size="1" slot="extension" class="elevation-2" style="border-bottom: 1px solid #424242;">
          <draggable v-bind="dragOptions" v-model="connections" class="v-tabs__container" @start="dragConnectionStart" @end="dragConnectionEnd">
            <v-tab v-for="(conn, index) in connections" :key="index" @click="changeConnection(index)" @contextmenu="showContextMenu($event, conn)" :title="Object.keys(conn.server).length > 0 ? '[' + conn.server.engine + ' ' + conn.server.version + ']' + ('hostname' in conn.server ? ': ' + conn.server.hostname : '') : ''" active-class="v-tabs-active" style="padding:0px 10px 0px 0px; float:left; height:100%; text-transform:none;">
              <span class="pl-2 pr-2" style="padding:0px!important; margin-left:15px;">
                <v-progress-circular v-if="conn.clientExecuting != null" indeterminate color="white" size="15" width="1.5" style="margin-right:10px"></v-progress-circular>
                <v-icon v-if="Object.keys(conn.server).length > 0" small :title="conn.server.shared ? 'Shared' : 'Personal'" :color="conn.server.shared ? '#EB5F5D' : 'warning'" style="margin-right:7px;">fas fa-server</v-icon>
                {{ Object.keys(conn.server).length > 0 ? conn.server.name : 'Connection ' + (conn.index) }}
                <v-btn title="Close Connection" small icon @click.prevent.stop="deleteConnection(index)" style="margin-left:10px;"><v-icon x-small style="padding-bottom:1px;">fas fa-times</v-icon></v-btn>
              </span>
            </v-tab>
          </draggable>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text title="New Connection" @click="newConnection()" style="font-size:16px; padding:0px; min-width:36px; height:36px; margin-top:6px;">+</v-btn>
        </v-tabs>
      </v-col>
      <v-col v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" cols="auto" class="flex-grow-0 flex-shrink-0">
        <div style="background-color:#2c2c2c; padding: 6px 0px 6px 6px; border-bottom: 1px solid #424242;">
          <v-menu v-model="queryFavMenu" offset-y :close-on-content-click="false" min-width="385px">
            <template v-slot:activator="{ attrs, on }">
              <v-btn @click="openFavourites()" v-bind="attrs" v-on="on" title="Query Favourites" style="min-width:52px"><v-icon small style="font-size:15px">far fa-star</v-icon></v-btn>
            </template>
            <v-autocomplete :loading="loadingFav" v-model="queryFavItem" @change="selectFavourite()" ref="queryFav" dense filled :items="queryFavItems" item-text="name" no-data-text="No queries found" return-object style="margin-top:7px; background-color:#2c2c2c" no-gutters></v-autocomplete>
          </v-menu>
        </div>
      </v-col>
      <v-col v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" cols="auto" class="flex-grow-0 flex-shrink-0">
        <div style="background-color:#2c2c2c; padding: 6px 0px 6px 6px; border-bottom: 1px solid #424242;">
          <v-btn :disabled="['query','stop'].includes(clientExecuting) || clientQuery['query'].length == 0" @click="beautifyQuery()" title="Beautify Query" style="min-width:52px"><v-icon small style="font-size:15px">fas fa-stream</v-icon></v-btn>
        </div>
      </v-col>
      <v-col v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" cols="auto" class="flex-grow-0 flex-shrink-0">
        <div style="background-color:#2c2c2c; padding: 6px 0px 6px 6px; border-bottom: 1px solid #424242;">
          <v-btn :disabled="['query','stop'].includes(clientExecuting) || clientQuery['query'].length == 0" @click="minifyQuery()" title="Minify Query" style="min-width:52px"><v-icon small style="font-size:15px">fas fa-remove-format</v-icon></v-btn>
        </div>
      </v-col>
      <v-col v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" cols="auto" class="flex-grow-0 flex-shrink-0">
        <div style="background-color:#2c2c2c; padding: 6px 0px 6px 6px; border-bottom: 1px solid #424242;">
          <v-divider class="mx-3" inset vertical style="height:29px; padding:0px; margin-top:4px; margin-left:5px!important; margin-right:5px!important;"></v-divider>
        </div>
      </v-col>
      <v-col v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" cols="auto" class="flex-grow-0 flex-shrink-0">
        <div style="background-color:#2c2c2c; padding: 6px 0px 6px 6px; border-bottom: 1px solid #424242;">
          <v-btn :disabled="['stop',null].includes(clientExecuting)" :loading="clientExecuting == 'stop'" @click="stopQuery()" title="Stop Query" style="min-width:52px"><v-icon small style="font-size:15px">fas fa-stop</v-icon></v-btn>
        </div>
      </v-col>
      <v-col v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" cols="auto" class="flex-grow-0 flex-shrink-0">
        <div style="background-color:#2c2c2c; padding: 6px 0px 6px 6px; border-bottom: 1px solid #424242;">
          <v-btn :loading="clientExecuting == 'explain'" :disabled="['query','stop'].includes(clientExecuting) || clientQuery['query'].length == 0" @click="explainQuery()" title="Explain Query" style="min-width:52px"><v-icon small style="font-size:15px">fas fa-chart-pie</v-icon></v-btn>
        </div>
      </v-col>
      <v-col v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" cols="auto" class="flex-grow-0 flex-shrink-0">
        <div style="background-color:#2c2c2c; padding:6px; border-bottom: 1px solid #424242;">
          <v-btn :loading="clientExecuting == 'query'" :disabled="['explain','stop'].includes(clientExecuting) || clientQuery['query'].length == 0" @click="runQuery()" title="Run Query"><v-icon small style="padding-right:10px; font-size:15px;">fas fa-bolt</v-icon>Run</v-btn>
        </div>
      </v-col>
    </v-row>
    <v-menu v-model="contextMenu" :position-x="contextMenuX" :position-y="contextMenuY" absolute offset-y style="z-index:10">
      <v-list style="padding:0px;">
        <v-list-item-group>
          <div v-for="item in contextMenuItems" :key="item">
            <v-list-item v-if="item != '|'" @click="contextMenuClicked(item)">
              <v-list-item-title style="font-size:0.9rem">{{ item }}</v-list-item-title>
            </v-list-item>
            <v-divider v-else></v-divider>
          </div>
        </v-list-item-group>
      </v-list>
    </v-menu>
  </div>
</template>

<style scoped>
.v-tabs-active { background-color: #353535; }
.v-list { padding:0px!important; }
</style>

<script>
import axios from 'axios'
import draggable from "vuedraggable";
import EventBus from '../js/event-bus'
import { mapFields } from '../js/map-fields'

export default {
  data() {
    return {
      dragOptions: {
        animation: 200,
      },
      loadingFav: false,
      // Query Favorite Menu
      queryFavItems: [],
      queryFavItem: {},
      queryFavMenu: false,
      // Connections - Context Menu
      contextMenu: false,
      contextMenuItems: [],
      contextMenuItem: {},
      contextMenuX: 0,
      contextMenuY: 0,
    }
  },
  components: { draggable },
  computed: {
    ...mapFields([
      'connections',
      'currentConn',
    ], { path: 'client/client' }),
    ...mapFields([
      'headerTabSelected',
      'sidebarMode',
      'sidebarLoading',
      'clientQuery',
      'clientExecuting',
      'server',
      'index',
    ], { path: 'client/connection' }),
    ...mapFields([
      'connections',
      'dialogOpened',
    ], { path: 'client/client' }),
  },
  mounted() {
    document.addEventListener("keydown", this.listeners, false)
  },
  beforeDestroy() {
    document.removeEventListener("keydown", this.listeners, false)
  },
  methods: {
    newConnection() {
      this.$store.dispatch('client/newConnection')
      this.sidebarLoading = false
    },
    changeConnection(index) {
      this.$store.dispatch('client/changeConnection', index)
    },
    dragConnectionStart(event) {
      this.$store.dispatch('client/changeConnection', event.oldIndex)
    },
    dragConnectionEnd(event) {
      let tabNumber = this.currentConn
      let oldIndex = event.oldIndex
      let newIndex = event.newIndex
      let tabActive = null;
  
      if (tabNumber === oldIndex) tabActive = newIndex;
      else if (tabNumber === newIndex && tabNumber < oldIndex) tabActive = tabNumber + 1;
      else if (tabNumber === newIndex && tabNumber > oldIndex) tabActive = tabNumber - 1;
      else if (tabNumber < oldIndex) tabActive = tabNumber + 1;
      else if (tabNumber > oldIndex) tabActive = tabNumber - 1;
      this.currentConn = tabActive;
    },
    deleteConnection(index) {
      axios.get('/client/close', { params: { connection: this.connections[index].id }})
      this.$store.dispatch('client/deleteConnection', index)
    },
    onContextMenu(event) {
      event.preventDefault()
    },
    runQuery() {
      EventBus.$emit('run-query')
    },
    explainQuery() {
      EventBus.$emit('explain-query')
    },
    stopQuery() {
      EventBus.$emit('stop-query')
    },
    beautifyQuery() {
      EventBus.$emit('beautify-query')
    },
    minifyQuery() {
      EventBus.$emit('minify-query')
    },
    openFavourites() {
      this.queryFavItem = {}
      if (this.queryFavMenu) return
      this.loadingFav = true
      requestAnimationFrame(() => {
        if (typeof this.$refs.queryFav !== 'undefined') setTimeout(() => {  this.$refs.queryFav.focus(); this.$refs.queryFav.isMenuActive = true; },100)
      })
      // Get saved queries
      axios.get('/client/saved')
        .then((response) => {
          this.queryFavItems = response.data.saved
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loadingFav = false)
    },
    selectFavourite() {
      EventBus.$emit('select-favourite', this.queryFavItem.query)
      this.queryFavItem = {}
      this.queryFavMenu = false
    },
    // Listeners
    listeners(e) {
      // - New Connection -
      if (e.key.toLowerCase() == "." && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        if (!this.dialogOpened) this.newConnection()
      }
      // - Remove Connection -
      else if (e.key.toLowerCase() == "," && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        if (!this.dialogOpened) this.deleteConnection(this.currentConn)
      }
      // - Previous Connection -
      else if (e.key.toLowerCase() == "o" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        if (!this.dialogOpened && this.connections.length > 1 && this.currentConn != 0) this.changeConnection(this.currentConn - 1)
      }
      // - Next Connection -
      else if (e.key.toLowerCase() == "p" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        if (!this.dialogOpened && this.connections.length > 1 && this.currentConn != this.connections.length - 1) this.changeConnection(this.currentConn + 1)
      }
      // - Change Connection -
      else if (['1','2','3','4','5','6','7','8','9'].includes(e.key) && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        if (!this.dialogOpened && this.connections.length >= parseInt(e.key)) this.changeConnection(parseInt(e.key) - 1)
      }
    },
    showContextMenu(e, item) {
      e.preventDefault()
      this.contextMenuItems = 'hostname' in item.server ? ['Copy Credentials'] : ['']
      this.contextMenuItem = item.server
      this.contextMenuX = e.clientX
      this.contextMenuY = e.clientY
      this.contextMenu = true
    },
    contextMenuClicked(item) {
      if (item == 'Copy Credentials') {
        navigator.clipboard.writeText(this.contextMenuItem['hostname'] + ':' + this.contextMenuItem['port'])
      }
    },
  },
}
</script>