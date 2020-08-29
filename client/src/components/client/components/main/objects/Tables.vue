<template>
  <div style="height:100%">
    <!------------>
    <!-- TABLES -->
    <!------------>
    <ag-grid-vue ref="agGridObjectTables" suppressColumnVirtualisation @grid-ready="onGridReady" @new-columns-loaded="onNewColumnsLoaded" @cell-key-down="onCellKeyDown" style="width:100%; height:calc(100% - 36px);" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" rowDeselection="true" :stopEditingWhenGridLosesFocus="true" :columnDefs="objectHeaders.tables" :rowData="objectItems.tables"></ag-grid-vue>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn @click="refresh" text small title="Refresh rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBar.objects.tables }}</div>
        </v-col>
      </v-row>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

import {AgGridVue} from "ag-grid-vue";
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'objectHeaders',
      'objectItems',
      'server',
      'database',
      'treeviewSelected',
      'bottomBar',
      'gridApi',
      'columnApi',
    ], { path: 'client/connection' }),
  },
  mounted () {
    EventBus.$on('GET_OBJECT_TABLES', this.getTables);
  },
  methods: {
   onGridReady(params) {
      this.gridApi.object.tables = params.api
      this.columnApi.object.tables = params.columnApi
      this.$refs['agGridObjectTables'].$el.addEventListener('click', this.onGridClick)
      this.gridApi.object.tables.showLoadingOverlay()
    },
    onNewColumnsLoaded() {
      if (this.gridApi.object.tables != null) this.resizeTable()
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.object.tables.deselectAll()
      }
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.object.tables.getAllColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.object.tables.autoSizeColumns(allColumnIds);
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        navigator.clipboard.writeText(e.value)

        // Highlight cells
        e.event.originalTarget.classList.add('ag-cell-highlight');
        e.event.originalTarget.classList.remove('ag-cell-highlight-animation')

        // Add animation
        window.setTimeout(function () {
            e.event.originalTarget.classList.remove('ag-cell-highlight')
            e.event.originalTarget.classList.add('ag-cell-highlight-animation')
            e.event.originalTarget.style.transition = "background-color " + 200 + "ms"

            // Remove animation
            window.setTimeout(function () {
                e.event.originalTarget.classList.remove('ag-cell-highlight-animation')
                e.event.originalTarget.style.transition = null;
            }, 200);
        }, 200);
      }
    },
    getTables() {
      const payload = {
        server: this.server.id,
        database: this.database,
        object: 'table',
      }
      axios.get('/client/objects', { params: payload })
        .then((response) => {
          this.parseTables(response.data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('SEND_NOTIFICATION', error.response.data.message, 'error')
        })
    },
    parseTables(data) {
      // Parse Info
      this.infoHeaders.events = [
        { text: 'Name', value: 'event_name' },
        { text: 'Type', value: 'event_type' },
        { text: 'Execute At', value: 'execute_at' },
        { text: 'Interval Value', value: 'interval_value' },
        { text: 'Interval Field', value: 'interval_field' },
        { text: 'Starts', value: 'starts' },
        { text: 'Ends', value: 'ends' },
        { text: 'On Completion', value: 'on_completion' },
        { text: 'Definer', value: 'definer' },
        // { text: 'Character Set Client', value: 'character_set_client' },
        { text: 'Collation Connection', value: 'collation_connection' },
        // { text: 'Database Collation', value: 'database_collation' },
        { text: 'Created', value: 'created' }
      ]
      let info = JSON.parse(data.info)
      this.infoItems.events = [info]

      // Parse Syntax
      this.infoEditor.events = info.syntax
      this.editor.setValue(info.syntax, -1)
      this.editor.focus()
    },
    refresh() {

    },
  }
}
</script>