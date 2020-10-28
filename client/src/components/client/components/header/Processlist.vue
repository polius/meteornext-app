<template>
  <div>
    <v-dialog v-model="dialog" max-width="80%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text"><v-icon small style="padding-right:10px; padding-bottom:2px">fas fa-server</v-icon>Processlist</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn color="primary" :title="stopped ? 'Start processlist retrieval' : 'Stop processlist retrieval'" style="margin-right:10px;"><v-icon small style="padding-right:10px">{{ stopped ? 'fas fa-play' : 'fas fa-stop'}}</v-icon>{{ stopped ? 'START' : 'STOP' }}</v-btn>
          <v-btn color="primary" style="margin-right:10px;"><v-icon small style="padding-right:10px">fas fa-arrow-down</v-icon>Export</v-btn>
          <v-btn color="primary"><v-icon small style="padding-right:10px; font-size:14px;">fas fa-cog</v-icon>Settings</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field v-model="search" label="Search" outlined dense color="white" hide-details></v-text-field>
          <!-- <v-text-field v-model="refreshRate" label="Refresh rate (seconds)" outlined dense color="white" hide-details></v-text-field> -->
          <!-- <v-spacer></v-spacer> -->
          <v-btn @click="dialog = false" icon style="margin-left:5px"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <!-- <v-text-field ref="field" v-model="search" label="Filter..." solo dense clearable hide-details></v-text-field> -->
                <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" style="width:100%; height:70vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="header" :rowData="items"></ag-grid-vue>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped src="@/styles/agGridVue.css"></style>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'
import {AgGridVue} from "ag-grid-vue";

export default {
  data() {
    return {
      dialog: false,
      stopped: false,
      refreshRate: '5',
      // AG Grid
      gridApi: null,
      columnApi: null,
      search: '',
      header: [],
      items: [],
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('show-processlist', this.showDialog);
  },
  watch: {
    dialog: function(value) {
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 6}
        this.headerTab = tab[this.headerTabSelected]
      }
    }
  },
  methods: {
    showDialog() {
      this.dialog = true
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      this.resizeTable()
    },
    resizeTable() {
      this.$nextTick(() => {
        if (this.gridApi != null) {
          if (this.items.length == 0) this.gridApi.sizeColumnsToFit()
          else {
            let allColIds = this.columnApi.getAllColumns().map(column => column.colId)
            this.columnApi.autoSizeColumns(allColIds)
          }
        }
      })
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        navigator.clipboard.writeText(e.value)

        // Highlight cells
        e.event.target.classList.add('ag-cell-highlight');
        e.event.target.classList.remove('ag-cell-highlight-animation')

        // Add animation
        window.setTimeout(function () {
            e.event.target.classList.remove('ag-cell-highlight')
            e.event.target.classList.add('ag-cell-highlight-animation')
            e.event.target.style.transition = "background-color " + 200 + "ms"

            // Remove animation
            window.setTimeout(function () {
                e.event.target.classList.remove('ag-cell-highlight-animation')
                e.event.target.style.transition = null;
            }, 200);
        }, 200);
      }
    },
  }
}
</script>