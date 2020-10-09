<template>
  <div style="height:100%">
    <div style="height: calc(100% - 84px)">
      <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="header" :rowData="rights['schema']"></ag-grid-vue>
    </div>
    <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
      <v-btn text small title="New User Right" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn text small title="Delete User Right" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
    </v-row>
  </div>
</template>

<style scoped src="@/styles/agGridVue.css"></style>

<script>
import { mapFields } from '../../../js/map-fields'
import {AgGridVue} from "ag-grid-vue";

export default {
  data() {
    return {
      // AG Grid
      gridApi: null,
      columnApi: null,
      header: [
        { headerName: 'Type', colId: 'type', field: 'type', sortable: true, filter: true, resizable: true, editable: false, 
          cellRenderer: function(params) {
            if (params.value == 'db') return '<i class="fas fa-database" title="Database" style="color:#ec644b; margin-right:10px"></i>Database';
            else if (params.value == 'table') return '<i class="fas fa-bars" title="Table" style="color:#F29111; margin-right:10px"></i>Table';
            else if (params.value == 'column') return '<i class="fas fa-grip-vertical" title="Column" style="color:#f2d984; margin-right:10px"></i>Column';
          },
          filterValueGetter: function (params) {
            if (params.data.type == 'db') return 'database'
            else return params.data.type;
          } 
        },
        { headerName: 'Schema', colId: 'schema', field: 'schema', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Rights', colId: 'rights', field: 'rights', sortable: true, filter: true, resizable: true, editable: false }
      ],
    }
  },
  components: { AgGridVue },
  props: { tab: Number },
  computed: {
    ...mapFields([
      'rights',
    ], { path: 'client/connection' }),
  },
  watch: {
    tab: function(value) {
      if (value == 2) this.resizeTable()
    }
  },
  methods: {
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      // this.resizeTable()
    },
    resizeTable() {
      this.$nextTick(() => {
        if (this.gridApi != null) {
          if (this.rights['schema'].length == 0) this.gridApi.sizeColumnsToFit()
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