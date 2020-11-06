<template>
  <v-row no-gutters>
    <v-col class="flex-grow-1 flex-shrink-1">
      <v-tabs v-model="currentConn" v-if="Object.keys(server).length != 0 || connections.length > 1" hide-slider show-arrows dense background-color="#2c2c2c" color="white" slider-color="#969696" slider-size="1" slot="extension" class="elevation-2" style="border-bottom: 1px solid #424242;">
        <draggable v-bind="dragOptions" v-model="connections" class="v-tabs__container" @start="dragConnectionStart" @end="dragConnectionEnd">
          <v-tab v-for="(conn, index) in connections" :key="index" @click="changeConnection(index)" :title="Object.keys(conn.server).length > 0 ? '[' + conn.server.type + ' ' + conn.server.version + '] ' + conn.server.host : ''" active-class="v-tabs-active" style="padding:0px 10px 0px 0px; float:left; height:100%; text-transform:none;">
            <span class="pl-2 pr-2" style="padding:0px!important; margin-left:15px;">
              <v-progress-circular v-if="conn.clientExecuting != null" indeterminate color="white" size="15" width="1.5" style="margin-right:5px; margin-bottom:2px"></v-progress-circular>
              {{ Object.keys(conn.server).length > 0 ? conn.server.name : 'Connection ' + (conn.index) }}
              <v-btn title="Close Connection" small icon @click.prevent.stop="deleteConnection(index)" style="margin-left:10px;"><v-icon x-small style="padding-bottom:1px;">fas fa-times</v-icon></v-btn></span>
          </v-tab>
        </draggable>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-btn text title="New Connection" @click="newConnection()" style="font-size:16px; padding:0px; min-width:36px; height:36px; margin-top:6px;">+</v-btn>
      </v-tabs>
    </v-col>
    <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
      <div v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" style="background-color:#2c2c2c; padding: 6px 0px 6px 6px; border-bottom: 1px solid #424242;">
        <v-btn :disabled="['query','stop'].includes(clientExecuting) || clientQuery['query'].length == 0" @click="beautifyQuery()" title="Beautify Query" style="min-width:52px"><v-icon small style="font-size:15px">fas fa-stream</v-icon></v-btn>
      </div>
    </v-col>
    <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
      <div v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" style="background-color:#2c2c2c; padding: 6px 0px 6px 6px; border-bottom: 1px solid #424242;">
        <v-btn :disabled="['query','stop'].includes(clientExecuting) || clientQuery['query'].length == 0" @click="minifyQuery()" title="Minify Query" style="min-width:52px"><v-icon small style="font-size:15px">fas fa-remove-format</v-icon></v-btn>
      </div>
    </v-col>
    <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
      <div v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" style="background-color:#2c2c2c; padding: 6px 0px 6px 6px; border-bottom: 1px solid #424242;">
        <v-divider class="mx-3" inset vertical style="height:29px; padding:0px; margin-top:4px; margin-left:5px!important; margin-right:5px!important;"></v-divider>
      </div>
    </v-col>
    <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
      <div v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" style="background-color:#2c2c2c; padding: 6px 0px 6px 6px; border-bottom: 1px solid #424242;">
        <v-btn :disabled="['stop',null].includes(clientExecuting)" :loading="clientExecuting == 'stop'" @click="stopQuery()" title="Stop Query" style="min-width:52px"><v-icon small style="font-size:15px">fas fa-stop</v-icon></v-btn>
      </div>
    </v-col>
    <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
      <div v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" style="background-color:#2c2c2c; padding: 6px 0px 6px 6px; border-bottom: 1px solid #424242;">
        <v-btn :loading="clientExecuting == 'explain'" :disabled="['query','stop'].includes(clientExecuting) || clientQuery['query'].length == 0" @click="explainQuery()" title="Explain Query" style="min-width:52px"><v-icon small style="font-size:15px">fas fa-chart-pie</v-icon></v-btn>
      </div>
    </v-col>
    <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
      <div v-if="sidebarMode == 'objects' && headerTabSelected == 'client'" style="background-color:#2c2c2c; padding:6px; border-bottom: 1px solid #424242;">
        <v-btn :loading="clientExecuting == 'query'" :disabled="['explain','stop'].includes(clientExecuting) || clientQuery['query'].length == 0" @click="runQuery()" title="Run Query"><v-icon small style="padding-right:10px; font-size:15px;">fas fa-bolt</v-icon>Run</v-btn>
      </div>
    </v-col>
  </v-row>
</template>

<style scoped>
.v-tabs-active {
  background-color:#303030;
}
</style>

<script>
import draggable from "vuedraggable";
import EventBus from '../js/event-bus'
import { mapFields } from '../js/map-fields'

export default {
  data() {
    return {
      dragOptions: {
        animation: 200,
      }
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
    ], { path: 'client/client' }),
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
      this.$store.dispatch('client/deleteConnection', index)
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
  },
}
</script>