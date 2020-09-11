<template>
  <v-row no-gutters>
    <v-col class="flex-grow-1 flex-shrink-1">
      <v-tabs v-model="currentConn" v-if="Object.keys(server).length != 0 || connections.length > 1" show-arrows dense background-color="#2c2c2c" color="white" slider-color="#969696" slider-size="1" slot="extension" class="elevation-2" style="border-bottom: 1px solid #424242;">
        <draggable v-model="connections" class="v-tabs__container" @start="dragConnectionStart" @end="dragConnectionEnd">
          <v-tab v-for="(conn, index) in connections" :key="index" @click="changeConnection(index)" :title="Object.keys(conn.server).length > 0 ? '[' + conn.server.type + '] ' + conn.server.host : ''" style="padding:0px 10px 0px 0px; float:left; height:100%; text-transform:none;">
            <span class="pl-2 pr-2" style="padding:0px!important; margin-left:15px;">{{ Object.keys(conn.server).length > 0 ? conn.server.name : 'Connection ' + (conn.index) }}<v-btn title="Close Connection" small icon @click.prevent.stop="deleteConnection(index)" style="margin-left:10px;"><v-icon x-small style="padding-bottom:1px;">fas fa-times</v-icon></v-btn></span>
          </v-tab>
        </draggable>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-btn text title="New Connection" @click="newConnection()" style="font-size:16px; padding:0px; min-width:36px; height:36px; margin-top:6px;">+</v-btn>
      </v-tabs>
    </v-col>
    <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
      <div v-if="treeviewMode == 'objects' && headerTabSelected == 'client'" style="background-color:#2c2c2c; padding:6px; border-bottom: 1px solid #424242;">
        <v-btn :loading="clientQueryExecuting" :disabled="clientQuery.length == 0" @click="runQuery()" title="Execute Query" style="margin-left:6px;"><v-icon small style="padding-right:10px;">fas fa-bolt</v-icon>Run</v-btn>
      </div>
    </v-col>
  </v-row>
</template>

<script>
import draggable from "vuedraggable";
import EventBus from '../js/event-bus'
import { mapFields } from '../js/map-fields'

export default {
  data() {
    return {
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
      'treeviewMode',
      'clientQuery',
      'clientQueryExecuting',
      'server',
      'index',
    ], { path: 'client/connection' }),
  },
  methods: {
    newConnection() {
      this.$store.dispatch('client/newConnection')
    },
    changeConnection(index) {
      this.$store.dispatch('client/changeConnection', index)
    },
    dragConnectionStart(event) {
      this.currentConn = event.oldIndex
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
      this.$store.dispatch('client/deleteConnection', index)
    },
    runQuery() {
      EventBus.$emit('RUN_QUERY')
    }
  },
}
</script>