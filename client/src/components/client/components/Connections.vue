<template>
  <v-row no-gutters>
    <v-col class="flex-grow-1 flex-shrink-1">
      <v-tabs v-if="Object.keys(server).length != 0" show-arrows dense background-color="#2c2c2c" color="white" v-model="currentConn" slider-color="#969696" slider-size="1" slot="extension" class="elevation-2" style="border-bottom: 1px solid #424242;">
        <v-tab v-for="(t, index) in connections" :key="index" @click="changeConnection(index)" :title="'Name: ' + t.server.name + '\nHost: ' + t.server.host" style="padding:0px 10px 0px 0px; text-transform:none;">
        <span class="pl-2 pr-2"><v-btn title="Close Connection" small icon @click.prevent.stop="removeConnection(index)" style="margin-right:10px;"><v-icon x-small style="padding-bottom:1px;">fas fa-times</v-icon></v-btn>{{ t.server.name }}</span>
        </v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-btn text title="New Connection" @click="newConnection()" style="height:100%; font-size:16px;">+</v-btn>
      </v-tabs>
    </v-col>
    <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
      <div v-if="headerTab == 0 && Object.keys(server).length != 0" style="background-color:#2c2c2c; padding:6px; border-bottom: 1px solid #424242;">
        <v-btn :loading="loadingQuery" :disabled="editorQuery.length == 0" @click="runQuery()" title="Execute Query" style="margin-left:6px;"><v-icon small style="padding-right:10px;">fas fa-bolt</v-icon>Run</v-btn>
      </div>
    </v-col>
  </v-row>
</template>

<script>
import EventBus from '../js/event-bus'

export default {
  data() {
    return {
    }
  },
  mounted () {
    // EventBus.$on(‘EVENT_NAME’, function (payLoad) {
    //   ...
    // });
  },
  computed: {
    connections () { return this.$store.getters['client/connections'] },
    currentConn () { return this.$store.getters['client/currentConn'] },
    headerTab () { return this.$store.getters['client/connection'].headerTab },
    editorQuery () { return this.$store.getters['client/connection'].editorQuery },
    loadingQuery () { return this.$store.getters['client/connection'].loadingQuery },
    server () { return this.$store.getters['client/connection'].server },
  },
  watch: {
    currentConn(value) {
      this.$store.dispatch('client/updateCurrentConn', value)
    }
  },
  methods: {
    changeConnection() {

    },
    removeConnection() {

    },
    runQuery() {
      EventBus.$emit('runQuery')
    }
  },
}
</script>