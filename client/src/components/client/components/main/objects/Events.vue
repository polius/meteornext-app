<template>
  <div style="height:100%">
    <!------------>
    <!-- EVENTS -->
    <!------------>
    <ag-grid-vue ref="agGridObjectsEvents" suppressColumnVirtualisation @grid-ready="onGridReady" @new-columns-loaded="onNewColumnsLoaded" @cell-key-down="onCellKeyDown" style="width:100%; height:calc(100% - 84px);" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" rowDeselection="true" :stopEditingWhenGridLosesFocus="true" :columnDefs="objectsHeaders.events" :rowData="objectsItems.events"></ag-grid-vue>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn :disabled="loading" @click="refresh" text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBar.objects.events }}</div>
        </v-col>
      </v-row>
    </div>
  </div>
</template>

<script>
import {AgGridVue} from "ag-grid-vue";
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      loading: false
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'tabObjectsSelected',
      'objectsHeaders',
      'objectsItems',
      'server',
      'treeviewSelected',
      'bottomBar',
      'gridApi',
      'columnApi',
    ], { path: 'client/connection' }),
  },
  watch: {
    tabObjectsSelected(val) {
      this.$nextTick(() => {
        if (val == 'events') this.resizeTable()
      })
    }
  },
  methods: {
   onGridReady(params) {
      this.gridApi.objects.events = params.api
      this.columnApi.objects.events = params.columnApi
      this.$refs['agGridObjectsEvents'].$el.addEventListener('click', this.onGridClick)
      this.gridApi.objects.events.showLoadingOverlay()
    },
    onNewColumnsLoaded() {
      if (this.gridApi.objects.events != null) this.resizeTable()
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.objects.events.deselectAll()
      }
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.objects.events.getAllColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.objects.events.autoSizeColumns(allColumnIds);
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
    refresh() {
      let promise = new Promise((resolve, reject) => {
        this.loading = true
        this.gridApi.objects.events.showLoadingOverlay()
        EventBus.$emit('GET_OBJECTS', resolve, reject)
      })
      promise.then(() => {})
        .catch(() => {})
        .finally(() => {
          this.gridApi.objects.events.hideOverlay() 
          this.loading = false 
        })
    },
  }
}
</script>