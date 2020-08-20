<template>
  <div>
    <!------------->
    <!-- CONTENT -->
    <!------------->
    <div style="height:calc(100% - 36px)">
      <div style="width:100%; height:100%">
        <div style="height:45px; background-color:#303030; margin:0px;">
          <v-row no-gutters>
            <v-col sm="auto">
              <div class="body-2" style="margin-top:13px; padding-left:10px; padding-right:10px;">Search:</div>
            </v-col>
            <v-col cols="2">
              <v-select v-model="contentSearchColumn" :items="contentColumnsName" dense solo hide-details height="35px" style="padding-top:5px;"></v-select>
            </v-col>
            <v-col cols="2">
              <v-select v-model="contentSearchFilter" :items="contentSearchFilterItems" dense solo hide-details height="35px" style="padding-top:5px; padding-left:5px;"></v-select>
            </v-col>
            <v-col v-if="contentSearchFilter != 'BETWEEN'">
              <v-text-field @keyup.enter="filterClick" :disabled="['IS NULL','IS NOT NULL'].includes(contentSearchFilter)" v-model="contentSearchFilterText" solo dense hide-details prepend-inner-icon="search" height="35px" style="padding-top:5px; padding-left:5px;"></v-text-field>
            </v-col>
            <v-col v-if="contentSearchFilter == 'BETWEEN'">
              <v-text-field v-model="contentSearchFilterText" @keyup.enter="filterClick" solo dense hide-details prepend-inner-icon="search" height="35px" style="padding-top:5px; padding-left:5px;"></v-text-field>
            </v-col>
            <v-col v-if="contentSearchFilter == 'BETWEEN'" sm="auto">
              <div class="body-2" style="margin-top:13px; padding-left:10px; padding-right:5px;">AND</div>
            </v-col>
            <v-col v-if="contentSearchFilter == 'BETWEEN'">
              <v-text-field v-model="contentSearchFilterText2" @keyup.enter="filterClick" solo dense hide-details prepend-inner-icon="search" height="35px" style="padding-top:5px; padding-left:5px;"></v-text-field>
            </v-col>
            <v-col sm="auto" justify="end">
              <v-btn @click="filterClick" style="margin-top:4px; margin-left:6px; margin-right:5px;">Filter</v-btn>
            </v-col>
          </v-row>
        </div>
        <ag-grid-vue ref="agGridContent" suppressColumnVirtualisation @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" @selection-changed="onSelectionChanged" @row-clicked="onRowClicked" @cell-editing-started="cellEditingStarted($event, true)" @cell-editing-stopped="cellEditingStopped($event, true)" style="width:100%; height:calc(100% - 48px);" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" rowDeselection="true" :stopEditingWhenGridLosesFocus="true" :columnDefs="contentHeaders" :rowData="contentItems"></ag-grid-vue>
      </div>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn @click="addRow" text small title="Add row" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="removeRow" :disabled="!isRowSelected" text small title="Remove selected row(s)" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="filterClick" text small title="Refresh rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="exportRows('content')" text small title="Export rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-arrow-down</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBarContent['status']=='success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:5px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBarContent['status']=='failure'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:1px; padding-right:5px;">fas fa-times-circle</v-icon>
            <span :title="bottomBarContent['text']">{{ bottomBarContent['text'] }}</span>
          </div>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBarContent['info'] }}</div>
        </v-col>
      </v-row>
    </div>
    <!------------->
    <!-- DIALOGS -->
    <!------------->
    <v-dialog v-model="editDialog" persistent max-width="80%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">{{ editDialogTitle }}</div>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:10px; margin-bottom:15px;">
                  <div style="margin-left:auto; margin-right:auto; height:60vh; width:100%">
                    <div id="editDialogEditor" style="float:left;"></div>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn @click="editDialogSubmit" color="primary">Save</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn @click="editDialogCancel" outlined color="#e74d3c">Cancel</v-btn>
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
// import axios from 'axios'

import {AgGridVue} from "ag-grid-vue";
// import EventBus from './event-bus'

export default {
  data() {
    return {
    }
  },
  components: { AgGridVue },
  mounted () {
    // EventBus.$on(‘EVENT_NAME’, function (payLoad) {
    //   ...
    // });
  },
  computed: {
    clientHeaders () { return this.$store.getters['client/connection'].clientHeaders },
    clientItems () { return this.$store.getters['client/connection'].clientItems },
    editDialog () { return this.$store.getters['client/connection'].editDialog },
    editDialogTitle () { return this.$store.getters['client/connection'].editDialogTitle },
  },
  watch: {
    // currentConn(value) {
    //   this.$store.dispatch('client/updateCurrentConn', value)
    // }
  },
  methods: {
   onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      // this.$refs['agGrid' + object.charAt(0).toUpperCase() + object.slice(1)].$el.addEventListener('click', this.onGridClick)
      if (['structure','content'].includes(this.tabSelected)) this.gridApi.showLoadingOverlay()
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
    editDialogSubmit() {
      this.editDialog = false
      let nodes = this.gridApi.getSelectedNodes()
      for (let i = 0; i < nodes.length; ++i) nodes[i].setSelected(false)
      let focusedCell = this.gridApi.getFocusedCell()
      let currentNode = this.gridApi.getDisplayedRowAtIndex(focusedCell.rowIndex)
      currentNode.setSelected(true)
      currentNode.setDataValue(focusedCell.column.colId, this.editDialogEditor.getValue())
      setTimeout(() => {
        this.gridApi.startEditingCell({
          rowIndex: focusedCell.rowIndex,
          colKey: focusedCell.column.colId
        })
      }, 100)
    },
    editDialogCancel() {
      this.editDialog = false
      this.editDialogEditor.setValue('')
    },
  },
}
</script>