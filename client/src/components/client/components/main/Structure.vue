<template>
  <div style="height:100%">
    <!--------------->
    <!-- STRUCTURE -->
    <!--------------->
    <v-tabs show-arrows dense background-color="#303030" color="white" slider-color="white" slider-size="1" slot="extension" class="elevation-2">
      <v-tabs-slider></v-tabs-slider>
      <v-tab @click="tabStructureColumns()"><span class="pl-2 pr-2">Columns</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabStructureIndexes()"><span class="pl-2 pr-2">Indexes</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabStructureFK()"><span class="pl-2 pr-2">Foreign Keys</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabStructureTriggers()"><span class="pl-2 pr-2">Triggers</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
    </v-tabs>
    <!---------------->
    <!-- COMPONENTS -->
    <!---------------->
    <Columns v-show="tabStructureSelected == 'columns'"/>
    <Indexes v-show="tabStructureSelected == 'indexes'"/>
    <FKs v-show="tabStructureSelected == 'fks'"/>
    <Triggers v-show="tabStructureSelected == 'triggers'"/>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" persistent max-width="50%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">Unable to apply changes</div>
              <v-flex xs12>
                <v-form style="margin-top:20px; margin-bottom:15px;">
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

<script>
import axios from 'axios'

import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import Columns from './structure/Columns'
import Indexes from './structure/Indexes'
import FKs from './structure/FKs'
import Triggers from './structure/Triggers'

export default {
  data() {
    return {
      // Dialog
      dialog: false,
      dialogText: '',
    }
  },
  components: { Columns, Indexes, FKs, Triggers },
  computed: {
    ...mapFields([
        'tabStructureSelected',
        'bottomBar',
        'gridApi',
        'columnApi',
        'structureHeaders',
        'structureItems',
        'treeviewSelected',
        'server',
        'database',
    ], { path: 'client/connection' }),
  },
  mounted () {
    EventBus.$on('GET_STRUCTURE', this.getStructure);
    EventBus.$on('EXECUTE_STRUCTURE', this.execute);
  },
  methods: {
    tabStructureColumns() {
      this.tabStructureSelected = 'columns'
    },
    tabStructureIndexes() {
      this.tabStructureSelected = 'indexes'
    },
    tabStructureFK() {
      this.tabStructureSelected = 'fks'
    },
    tabStructureTriggers() {
      this.tabStructureSelected = 'triggers'
    },
    getStructure() {
      this.gridApi.structure[this.tabStructureSelected].showLoadingOverlay()
      this.bottomBar.structure[this.tabStructureSelected] = { status: '', text: '', info: '' }
      // Retrieve Tables
      axios.get('/client/structure', { params: { server: this.server.id, database: this.database, table: this.treeviewSelected['name'] } })
        .then((response) => {
          this.parseStructure(response.data)
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.gridApi.structure[this.tabStructureSelected].hideOverlay()
        })
    },
    parseStructure(data) {
      // Parse Columns
      var columns_items = JSON.parse(data.columns)
      var columns_headers = []
      var column_names = []
      if (columns_items.length > 0) {
        var columns_keys = Object.keys(columns_items[0])
        for (let i = 0; i < columns_keys.length; ++i) {
          let field = columns_keys[i].trim()
          columns_headers.push({ headerName: columns_keys[i], colId: field, field: field, sortable: false, filter: false, resizable: true, editable: false })
        }
        for (let i = 0; i < columns_items.length; ++i) {
          column_names.push(columns_items[i]['Name'])
        }
      }
      columns_headers[0]['rowDrag'] = true
      this.columnItems = column_names
      this.structureHeaders.columns = columns_headers
      this.structureItems.columns = columns_items
      if (columns_items.length == 0) this.gridApi.structure.columns.showNoRowsOverlay()

      // Parse Indexes
      var indexes_items = JSON.parse(data.indexes)
      var indexes_headers = []
      if (indexes_items.length > 0) {
        var indexes_keys = Object.keys(indexes_items[0])
        for (let i = 0; i < indexes_keys.length; ++i) {
          let field = indexes_keys[i].trim()
          indexes_headers.push({ headerName: indexes_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: false })
        }
      }
      this.structureHeaders.indexes = indexes_headers
      this.structureItems.indexes = indexes_items
      if (indexes_items.length == 0) this.gridApi.structure.indexes.showNoRowsOverlay()

      // Parse Foreign Keys
      var fks_items = JSON.parse(data.fks)
      var fks_headers = []
      if (fks_items.length > 0) {
        var fks_keys = Object.keys(fks_items[0])
        for (let i = 0; i < fks_keys.length; ++i) {
          let field = fks_keys[i].trim()
          fks_headers.push({ headerName: fks_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: false })
        }
      }
      this.structureHeaders.fks = fks_headers
      this.structureItems.fks = fks_items
      if (fks_items.length == 0) this.gridApi.structure.fks.showNoRowsOverlay()

      // Parse Triggers
      var triggers_items = JSON.parse(data.triggers)
      var triggers_headers = []
      if (triggers_items.length > 0) {
        var triggers_keys = Object.keys(triggers_items[0])
        for (let i = 0; i < triggers_keys.length; ++i) {
          let field = triggers_keys[i].trim()
          triggers_headers.push({ headerName: triggers_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: false })
        }
      }
      this.structureHeaders.triggers = triggers_headers
      this.structureItems.triggers = triggers_items
      if (triggers_items.length == 0) this.gridApi.structure.triggers.showNoRowsOverlay()
    },
    execute(query, resolve, reject) {
      // Execute Query
      const payload = {
        server: this.server.id,
        database: this.database,
        queries: [query]
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          // Show Loading Overlay
          this.gridApi.structure[this.tabStructureSelected].showLoadingOverlay()
          // Hide Dialogs
          this.dialog = false
          // Get Response Data
          let data = JSON.parse(response.data.data)
          // Get Structure
          this.getStructure()
          // Build BottomBar
          this.parseBottomBar(data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            let data = JSON.parse(error.response.data.data)
            // Build BottomBar
            this.parseBottomBar(data)
            // Show error
            this.dialogText = data[0]['error']
            this.dialog = true
            // Reject promise
            reject()
          }
        })
        .finally(() => { resolve() })
    },
    parseBottomBar(data) {
      var elapsed = null
      if (data[data.length-1]['time'] !== undefined) {
        elapsed = 0
        for (let i = 0; i < data.length; ++i) {
          elapsed += parseFloat(data[i]['time'])
        }
        elapsed /= data.length
      }
      this.bottomBar.structure[this.tabStructureSelected]['status'] = data[0]['error'] === undefined ? 'success' : 'failure'
      this.bottomBar.structure[this.tabStructureSelected]['text'] = data[0]['query']
      if (elapsed != null) this.bottomBar.structure[this.tabStructureSelected]['info'] = elapsed.toString() + 's elapsed'
    },
  },
}
</script>