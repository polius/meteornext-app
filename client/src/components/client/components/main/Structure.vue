<template>
  <div>
    <!--------------->
    <!-- STRUCTURE -->
    <!--------------->
    <div style="height:calc(100% - 36px)">
      <div style="width:100%; height:100%;">
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
        <ag-grid-vue ref="agGridStructure" @grid-ready="onGridReady" @row-data-changed="onFirstDataRendered" @first-data-rendered="onFirstDataRendered" @cell-key-down="onCellKeyDown" @row-double-clicked="onRowDoubleClicked" @row-drag-end="onRowDragEnd" style="width:100%; height:calc(100% - 48px);" class="ag-theme-alpine-dark" suppressNoRowsOverlay="true" rowDragManaged="true" suppressMoveWhenRowDragging="true" rowHeight="35" headerHeight="35" rowSelection="simple" :stopEditingWhenGridLosesFocus="true" :columnDefs="structureHeaders" :rowData="structureItems"></ag-grid-vue>
      </div>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn @click="addStructure" text small :title="tabStructureSelected == 'columns' ? 'New Column' : tabStructureSelected == 'indexes' ? 'New Index' : tabStructureSelected == 'fks' ? 'New Foreign Key' : 'New Trigger'" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="removeStructure" text small :title="tabStructureSelected == 'columns' ? 'Remove Column' : tabStructureSelected == 'indexes' ? 'Remove Index' : tabStructureSelected == 'fks' ? 'Remove Foreign Key' : 'Remove Trigger'" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="getStructure" text small :title="tabStructureSelected == 'columns' ? 'Refresh Columns' : tabStructureSelected == 'indexes' ? 'Refresh Indexes' : tabStructureSelected == 'fks' ? 'Refresh Foreign Keys' : 'Refresh Triggers'" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBarStructure['status']=='success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:5px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBarStructure['status']=='failure'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:1px; padding-right:5px;">fas fa-times-circle</v-icon>
            <span :title="bottomBarStructure['text']">{{ bottomBarStructure['text'] }}</span>
          </div>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBarStructure['info'] }}</div>
        </v-col>
      </v-row>
    </div>
    <!------------->
    <!-- DIALOGS -->
    <!------------->
    <v-dialog v-model="structureDialog" persistent max-width="60%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ structureDialogTitle }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loadingDialog" @click="structureDialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <!-- <div class="text-h6" style="font-weight:400;">{{ structureDialogTitle }}</div> -->
              <v-flex xs12>
                <v-form v-if="tabStructureSelected == 'columns'" ref="structureDialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <v-text-field ref="structureDialogFormFocus" v-model="structureDialogItem.name" :rules="[v => !!v || '']" label="Name" required style="padding-top:0px;"></v-text-field>
                  <v-autocomplete v-model="structureDialogItem.type" :items="structureDialogColumnTypes" :rules="[v => !!v || '']" label="Type" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                  <v-text-field v-model="structureDialogItem.length" label="Length" required style="padding-top:0px;"></v-text-field>
                  <v-autocomplete :disabled="!['CHAR','VARCHAR','TEXT','TINYTEXT','MEDIUMTEXT','LONGTEXT','SET','ENUM'].includes(structureDialogItem.type)" v-model="structureDialogItem.collation" :items="structureDialogCollations" label="Collation" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                  <v-text-field :disabled="structureDialogItem.auto_increment" v-model="structureDialogItem.default" label="Default" required style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="structureDialogItem.comment" label="Comment" required style="padding-top:0px;"></v-text-field>
                  <v-checkbox :disabled="!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT','DECIMAL','FLOAT','DOUBLE'].includes(structureDialogItem.type)" v-model="structureDialogItem.unsigned" label="Unsigned" color="info" style="margin-top:0px; padding-top:0px;" hide-details></v-checkbox>
                  <v-checkbox :disabled="!['DATETIME','TIMESTAMP'].includes(structureDialogItem.type)" v-model="structureDialogItem.current_timestamp" label="On Update Current Timestamp" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                  <v-checkbox :disabled="!['TINYINT','SMALLINT','MEDIUMINT','INT','BIGINT'].includes(structureDialogItem.type)" v-model="structureDialogItem.auto_increment" label="Auto Increment" @change="structureDialogItem.auto_increment ? structureDialogItem.default = '' : ''" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                  <v-checkbox v-model="structureDialogItem.null" label="Allow Null" color="info" style="margin-top:0px;" hide-details></v-checkbox>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loadingDialog" @click="structureDialogSubmit" color="primary">Save</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loadingDialog" @click="structureDialogCancel" outlined color="#e74d3c">Cancel</v-btn>
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
    }
  },
}
</script>