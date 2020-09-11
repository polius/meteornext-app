<template>
  <div style="height:100%">
    <!------------->
    <!-- OBJECTS -->
    <!------------->
    <v-tabs v-model="objectsTab" show-arrows dense background-color="#303030" color="white" slider-color="white" slider-size="1" slot="extension" class="elevation-2">
      <v-tabs-slider></v-tabs-slider>
      <v-tab @click="tabObjects('databases')"><span class="pl-2 pr-2">Databases</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabObjects('tables')"><span class="pl-2 pr-2">Tables</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabObjects('views')"><span class="pl-2 pr-2">Views</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabObjects('triggers')"><span class="pl-2 pr-2">Triggers</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabObjects('functions')"><span class="pl-2 pr-2">Functions</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabObjects('procedures')"><span class="pl-2 pr-2">Procedures</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabObjects('events')"><span class="pl-2 pr-2">Events</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
    </v-tabs>
    <!---------------->
    <!-- COMPONENTS -->
    <!---------------->
    <Databases v-show="tabObjectsSelected == 'databases'" />
    <Tables v-show="tabObjectsSelected == 'tables'" />
    <Views v-show="tabObjectsSelected == 'views'" />
    <Triggers v-show="tabObjectsSelected == 'triggers'" />
    <Functions v-show="tabObjectsSelected == 'functions'" />
    <Procedures v-show="tabObjectsSelected == 'procedures'" />
    <Events v-show="tabObjectsSelected == 'events'" />
  </div>
</template>

<script>
import axios from 'axios'
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import Databases from './objects/Databases'
import Tables from './objects/Tables'
import Views from './objects/Views'
import Triggers from './objects/Triggers'
import Functions from './objects/Functions'
import Procedures from './objects/Procedures'
import Events from './objects/Events'

export default {
  data() {
    return {
    }
  },
  components: { Databases, Tables, Views, Triggers, Functions, Procedures, Events },
  computed: {
    ...mapFields([
      'objectsTab',
      'tabObjectsSelected',
      'server',
      'database',
      'objectsHeaders',
      'objectsItems',
      'bottomBar',
    ], { path: 'client/connection' }),
  },
  mounted() {
    // Register Event
    EventBus.$on('GET_OBJECTS', this.getObjects);
  },
  methods: {
    tabObjects(object) {
      this.tabObjectsSelected = object
    },
    getObjects(resolve, reject) {
      const payload = {
        server: this.server.id,
        database: this.database,
        detailed: true
      }
      axios.get('/client/objects', { params: payload })
        .then((response) => {
          for (let [key, value] of Object.entries(response.data)) this.parseObjects(key, value)
          resolve()
        })
        .catch((error) => {
          console.log(error)
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('SEND_NOTIFICATION', error.response.data.message, 'error')
          reject()
        })      
    },
    parseObjects(object, value) {
      let data = JSON.parse(value)
      // Parse each object
      this.objectsHeaders[object] = []
      this.objectsItems[object] = []

      if (data.length > 0) {
        for (let [key] of Object.entries(data[0])) {
          let column = { headerName: this.parseHeaderName(key), colId: key.trim(), field: key.trim(), sortable: true, filter: true, resizable: true, editable: false }
          if (object == 'tables' && ['data_length','index_length','total_length'].includes(key)) {
            column.valueGetter = (params) => {
              return this.parseBytes(params.data[params.colDef.field])
            }
            column.comparator = this.compareValues
          }
          this.objectsHeaders[object].push(column)
        }
        this.objectsItems[object] = data
      }
      this.bottomBar.objects[object] = data.length + ' record(s)'
    },
    parseHeaderName(rawName) {
      let name = rawName.replaceAll('_', ' ')
      name = name.split(" ")
      for (let i = 0; i < name.length; i++) name[i] = name[i][0].toUpperCase() + name[i].substr(1)
      return name.join(" ").trim()
    },
    parseBytes(value) {
      if (value/1024 < 1) return value + ' B'
      else if (value/1024/1024 < 1) return value/1024 + ' KB'
      else if (value/1024/1024/1024 < 1) return value/1024/1024 + ' MB'
      else if (value/1024/1024/1024/1024 < 1) return value/1024/1024/1024 + ' GB'
      else return value/1024/1024/1024/1024 + ' TB' 
    },
    compareValues(value1, value2) {
      // Check NULL & Empty Values
      if ((value1 === null && value2 === null) || (value1 !== null && value2 !== null && value1.toString().trim() == '' && value2.toString().trim() == '')) return 0
      if ((value1 === null) || (value1.toString().trim() == '')) return -1
      if ((value2 === null) || (value2.toString().trim() == '')) return 1

      // Check NOT NULL Values
      if (!isNaN(parseFloat(value1)) && !isNaN(parseFloat(value2))) return parseFloat(value1) - parseFloat(value2)
      else return value1.toString().localeCompare(value2.toString())
    }
  }
}
</script>