<template>
  <v-main>
    <div>
      <v-tabs show-arrows background-color="#9b59b6" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
        <v-tabs-slider></v-tabs-slider>
          <v-tab @click="tabClient()"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-bolt</v-icon>CLIENT</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <!-- <v-tab v-if="treeviewMode == 'objects' && database.length > 0 && treeview.length == 0"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-layer-group</v-icon>Objects</span></v-tab> -->
          <!-- <v-divider v-if="treeviewMode == 'objects' && database.length > 0 && treeview.length == 0" class="mx-3" inset vertical></v-divider> -->
          <v-tab @click="tabStructure()" :disabled="treeviewMode != 'objects' || treeview.length == 0 || ('children' in treeviewSelected) || treeviewSelected['type'] != 'Table'"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-dice-d6</v-icon>Structure</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab @click="tabContent()" :disabled="treeviewMode != 'objects' || treeview.length == 0 || ('children' in treeviewSelected) || !(['Table','View'].includes(treeviewSelected['type']))"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-bars</v-icon>Content</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab @click="tabInfo(treeviewSelected['type'].toLowerCase())" :disabled="treeviewMode != 'objects' || treeview.length == 0 || ('children' in treeviewSelected) || !(['Table','View','Trigger','Function','Procedure','Event'].includes(treeviewSelected['type']))"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-italic</v-icon>Info</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-spacer></v-spacer>
          <v-tab title="Query History" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-history</v-icon></span></v-tab>
          <v-tab title="Saved Queries" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-star</v-icon></span></v-tab>
          <v-tab :disabled="treeviewMode == 'servers'" title="User Rights" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-shield-alt</v-icon></span></v-tab>
        </v-tabs>
    </div>
    <v-container fluid>
      <v-main style="padding-top:0px; padding-bottom:0px;">
        <div style="margin: -12px;">
          <div ref="masterDiv" style="height: calc(100vh - 112px);">
            <!----------------->
            <!-- CONNECTIONS -->
            <!----------------->
            <v-row no-gutters>
              <v-col class="flex-grow-1 flex-shrink-1">
                <v-tabs v-if="connections.length > 0" show-arrows dense background-color="#2c2c2c" color="white" v-model="currentConn" slider-color="#969696" slider-size="1" slot="extension" class="elevation-2" style="border-bottom: 1px solid #424242;">
                  <v-tab v-for="(t, index) in connections" :key="index" @click="changeConnection(index)" :title="'Name: ' + t.server.name + '\nHost: ' + t.server.host" style="padding:0px 10px 0px 0px; text-transform:none;">
                    <span class="pl-2 pr-2"><v-btn title="Close Connection" small icon @click.prevent.stop="removeConnection(index)" style="margin-right:10px;"><v-icon x-small style="padding-bottom:1px;">fas fa-times</v-icon></v-btn>{{ t.server.name }}</span>
                  </v-tab>
                  <v-divider class="mx-3" inset vertical></v-divider>
                  <v-btn text title="New Connection" @click="newConnection()" style="height:100%; font-size:16px;">+</v-btn>
                </v-tabs>
              </v-col>
              <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
                <div v-if="tabSelected == 'client' && connections.length > 0" style="background-color:#2c2c2c; padding:6px; border-bottom: 1px solid #424242;">
                  <v-btn :loading="loadingQuery" :disabled="editorQuery.length == 0" @click="runQuery()" title="Execute Query" style="margin-left:6px;"><v-icon small style="padding-right:10px;">fas fa-bolt</v-icon>Run</v-btn>
                </div>
              </v-col>
            </v-row>
            <Splitpanes :style="connections.length > 0 ? 'height:calc(100% - 49px)' : 'height:100%'">
              <Pane size="20" min-size="0">
                <!------------->
                <!-- SIDEBAR -->
                <!------------->
                <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
                  <div style="height:calc(100% - 36px)">
                    <v-select v-model="database" @change="getObjects" solo :disabled="databaseItems.length == 0"  :items="databaseItems" label="Database" hide-details background-color="#303030" height="48px" style="padding:10px;"></v-select>
                    <div v-if="treeviewMode == 'servers' || database.length != 0" class="subtitle-2" style="padding-left:10px; padding-top:8px; color:rgb(222,222,222);">{{ (treeviewMode == 'servers') ? 'SERVERS' : 'OBJECTS' }}</div>
                    <div v-else-if="database.length == 0" class="body-2" style="padding-left:20px; padding-top:8px; padding-bottom:1px; color:rgb(222,222,222);"><v-icon small style="padding-right:10px; padding-bottom:4px;">fas fa-arrow-up</v-icon>Select a database</div>
                    <v-treeview :disabled="loadingServer" @contextmenu="show" :active.sync="treeview" item-key="id" :open="treeviewOpen" :items="treeviewItems" :search="treeviewSearch" activatable open-on-click transition class="clear_shadow" style="height:calc(100% - 158px); padding-top:7px; width:100%; overflow-y:auto;">
                      <template v-slot:label="{item, open}">
                        <v-btn text @click="treeviewClick(item)" @contextmenu="show" style="font-size:14px; text-transform:none; font-weight:400; width:100%; justify-content:left; padding:0px;"> 
                          <v-icon v-if="!item.type" small style="padding:10px;">
                            {{ open ? 'mdi-folder-open' : 'mdi-folder' }}
                          </v-icon>
                          <v-icon v-else small :title="item.type" :color="treeviewColor[item.type]" style="padding:10px;">
                            {{ treeviewImg[item.type] }}
                          </v-icon>
                          {{item.name}}
                          <v-spacer></v-spacer>
                          <v-progress-circular v-if="loadingServer && item.id == treeview[0]" indeterminate size="16" width="2" color="white" style="margin-right:10px;"></v-progress-circular>
                        </v-btn>
                      </template>
                    </v-treeview>
                    <v-menu v-model="showMenu" :position-x="x" :position-y="y" absolute offset-y>
                      <v-list style="padding:0px;">
                        <v-list-item v-for="menuItem in menuItems" :key="menuItem" @click="clickAction">
                          <v-list-item-title>{{menuItem}}</v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </v-menu>
                    <v-text-field :disabled="treeviewMode == 'objects' && database.length == 0" v-model="treeviewSearch" label="Search" dense solo hide-details height="38px" style="float:left; width:100%; padding:10px;"></v-text-field>
                  </div>
                  <!--------------------->
                  <!-- LEFT BOTTOM BAR -->
                  <!--------------------->
                  <!-- SERVERS -->
                  <div v-if="treeviewMode == 'servers'" style="height:35px; border-top:2px solid #2c2c2c;">
                    <v-btn text small title="New Connection" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
                    <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                    <v-btn text small title="Remove Connection" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
                    <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
                    <v-btn text small title="Refresh Connections" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
                  </div>
                  <!-- OBJECTS -->
                  <div v-else-if="treeviewMode == 'objects'" style="height:35px; border-top:2px solid #2c2c2c;">
                    <!-- <v-btn text small title="Refresh Objects" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn> -->
                  </div>
                </div>
              </Pane>
              <Pane size="80" min-size="0">
                <div style="height:100%; width:100%">
                  <div style="height:calc(100% - 36px)">                  
                    <!------------>
                    <!-- CLIENT -->
                    <!------------>
                    <Splitpanes v-show="tabSelected == 'client'" horizontal @ready="initAceClient()">
                      <Pane size="50">
                        <div style="margin-left:auto; margin-right:auto; height:100%; width:100%">
                          <div id="editor" style="float:left"></div>
                        </div>
                      </Pane>
                      <Pane size="50" min-size="0">
                        <ag-grid-vue suppressColumnVirtualisation @grid-ready="onGridReady" @cell-editing-started="cellEditingStarted($event, false)" @cell-editing-stopped="cellEditingStopped($event, false)" @cell-key-down="onCellKeyDown" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :stopEditingWhenGridLosesFocus="true" :columnDefs="clientHeaders" :rowData="clientItems"></ag-grid-vue>
                      </Pane>
                    </Splitpanes>
                    <!--------------->
                    <!-- STRUCTURE -->
                    <!--------------->
                    <div v-show="tabSelected == 'structure'" style="width:100%; height:100%;">
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
                      <!-- <div style="width:100%; height:calc(100% - 85px); z-index:1; position:absolute; text-align:center;">
                        <v-progress-circular indeterminate color="#dcdcdc" width="2" style="height:100%;"></v-progress-circular>
                      </div>-->
                      <ag-grid-vue @column-resized="onColumnResized" @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" style="width:100%; height:calc(100% - 48px);" class="ag-theme-alpine-dark" suppressNoRowsOverlay="true" rowHeight="35" headerHeight="35" rowSelection="single" :stopEditingWhenGridLosesFocus="true" :columnDefs="structureHeaders" :rowData="structureItems"></ag-grid-vue>
                    </div>
                    <!------------->
                    <!-- CONTENT -->
                    <!------------->
                    <div v-show="tabSelected == 'content'" style="width:100%; height:100%">
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
                      <ag-grid-vue suppressColumnVirtualisation @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" @selection-changed="onSelectionChanged" @cell-editing-started="cellEditingStarted($event, true)" @cell-editing-stopped="cellEditingStopped($event, true)" style="width:100%; height:calc(100% - 48px);" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :stopEditingWhenGridLosesFocus="true" :columnDefs="contentHeaders" :rowData="contentItems"></ag-grid-vue>
                    </div>
                    <!---------->
                    <!-- INFO -->
                    <!---------->
                    <div v-show="tabSelected == 'table_info'" style="width:100%; height:100%">
                      <div class="subtitle-2" style="padding:10px; padding-left:15px; color:rgb(222,222,222);">TABLE SYNTAX</div>
                      <div style="margin-left:auto; margin-right:auto; height:calc(100% - 42px); width:100%">
                        <div id="infoEditor" style="float:left"></div>
                      </div>
                    </div>
                  </div>
                  <!---------------------->
                  <!-- RIGHT BOTTOM BAR -->
                  <!---------------------->
                  <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
                    <!-- CLIENT -->
                    <v-row v-if="tabSelected == 'client'" no-gutters style="flex-wrap: nowrap;">
                      <v-col v-if="clientItems.length > 0" cols="auto">
                        <v-btn text small title="Export rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-arrow-down</v-icon></v-btn>
                        <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                      </v-col>
                      <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
                        <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                          <v-icon v-if="bottomBarClient['status']=='success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:5px;">fas fa-check-circle</v-icon>
                          <v-icon v-else-if="bottomBarClient['status']=='failure'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:1px; padding-right:5px;">fas fa-times-circle</v-icon>
                          <span :title="bottomBarClient['text']">{{ bottomBarClient['text'] }}</span>
                        </div>
                      </v-col>
                      <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
                        <div class="body-2" style="text-align:right;">{{ bottomBarClient['info'] }}</div>
                      </v-col>
                    </v-row>
                    <!-- CONTENT -->
                    <v-row v-else-if="tabSelected == 'content'" no-gutters style="flex-wrap: nowrap;">
                      <v-col cols="auto">
                        <v-btn @click="addRow" text small title="Add row" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
                        <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                        <v-btn @click="removeRow" :disabled="!isRowSelected" text small title="Remove selected row(s)" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
                        <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
                        <v-btn @click="filterClick" text small title="Refresh rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
                        <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                        <v-btn text small title="Export rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-arrow-down</v-icon></v-btn>
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
                    <!-- STRUCTURE -->
                    <v-row v-else-if="tabSelected == 'structure'" no-gutters style="flex-wrap: nowrap;">
                      <v-col cols="auto">
                        <v-btn text small :title="tabStructureSelected == 'columns' ? 'New Column' : tabStructureSelected == 'indexes' ? 'New Index' : tabStructureSelected == 'fks' ? 'New Foreign Key' : 'New Trigger'" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
                        <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                        <v-btn text small :title="tabStructureSelected == 'columns' ? 'Remove Column' : tabStructureSelected == 'indexes' ? 'Remove Index' : tabStructureSelected == 'fks' ? 'Remove Foreign Key' : 'Remove Trigger'" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
                        <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
                        <v-btn text small :title="tabStructureSelected == 'columns' ? 'Refresh Columns' : tabStructureSelected == 'indexes' ? 'Refresh Indexes' : tabStructureSelected == 'fks' ? 'Refresh Foreign Keys' : 'Refresh Triggers'" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
                        <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
                      </v-col>
                    </v-row>
                  </div>
                </div>
              </Pane>
            </Splitpanes>
          </div>
          <v-dialog v-model="dialog" persistent max-width="50%">
            <v-card>
              <v-card-text style="padding:15px 15px 5px;">
                <v-container style="padding:0px">
                  <v-layout wrap>
                    <div class="text-h5">{{ dialogTitle }}</div>
                    <v-flex xs12>
                      <v-form ref="form" style="margin-top:20px; margin-bottom:15px;">
                        <div class="text-body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogText }}</div>
                      </v-form>
                      <v-divider></v-divider>
                      <div style="margin-top:15px;">
                        <v-row no-gutters>
                          <v-col v-if="dialogButtonText1.length > 0" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                            <v-btn @click="dialogSubmit(1)" color="primary">{{ dialogButtonText1 }}</v-btn>
                          </v-col>
                          <v-col v-if="dialogButtonText2.length > 0" style="margin-bottom:10px;">
                            <v-btn @click="dialogSubmit(2)" outlined color="#e74d3c">{{ dialogButtonText2 }}</v-btn>
                          </v-col>
                        </v-row>
                      </div>
                    </v-flex>
                  </v-layout>
                </v-container>
              </v-card-text>
            </v-card>
          </v-dialog>
          <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
            {{ snackbarText }}
            <v-btn color="white" text @click="snackbar = false">Close</v-btn>
          </v-snackbar>
        </div>
      </v-main>
    </v-container>
  </v-main>
</template>

<style scoped>
@import "../../../node_modules/ag-grid-community/dist/styles/ag-grid.css";
@import "../../../node_modules/ag-grid-community/dist/styles/ag-theme-alpine-dark.css";

::v-deep .splitpanes__pane {
  box-shadow: 0 0 3px rgba(0, 0, 0, .2) inset;
  justify-content: center;
  align-items: center;
  display: flex;
  position: relative;
}
::v-deep .splitpanes--vertical > .splitpanes__splitter {
  min-width: 2px;
}
::v-deep .splitpanes--horizontal > .splitpanes__splitter {
  min-height: 2px;
}
::v-deep .ace_editor {
  margin: auto;
  height: 100%;
  width: 100%;
  background: #272822;
}
::v-deep .ace_content {
  width: 100%;
  height: 100%;
}
::v-deep .v-treeview-node__root {
  min-height:30px;
}
::v-deep .v-treeview-node__toggle {
  width: 15px;
}

::v-deep .splitpanes__splitter {background-color:rgba(32, 32, 32, 0.2); position: relative; }
::v-deep .splitpanes__splitter:before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  transition: opacity 0.4s;
  background-color: rgba(32, 32, 32, 0.3);
  opacity: 0;
  z-index: 10;
}
::v-deep .splitpanes__splitter:hover:before  {opacity:1; }
::v-deep .splitpanes--vertical > .splitpanes__splitter:before { left:-3px; right:-3px; height:100%; }
::v-deep .splitpanes--horizontal > .splitpanes__splitter:before { top:-5px; bottom:-3px; width:100%; }

::v-deep .theme--dark.v-data-table.v-data-table--fixed-header thead th {
  background-color: #252525;
}
::v-deep .v-treeview-node__level {
  width: 10px;
}
::v-deep .v-label{
  font-size: 0.9rem;
}
::v-deep .v-list-item__title {
  font-size: 0.9rem;
}
::v-deep .v-list-item__content {
  padding:0px;
}
::v-deep .v-list-item {
  min-height:40px;
}
::v-deep .v-input {
  font-size: 0.9rem;
}
::v-deep .v-application .elevation-2 {
  box-shadow:none!important;
}
::v-deep .container {
  padding-bottom:0px;
}
::v-deep .v-text-field .v-input__control .v-input__slot {
  min-height: auto !important;
  display: flex !important;
  align-items: center !important;
}
::v-deep *
{
  will-change: auto !important;
}
::v-deep .ace_editor.ace_autocomplete {
  width: 512px;
}
/* AG GRID */
::v-deep .ag-theme-alpine-dark .ag-header-row {
  font-size: 13px;
  font-weight: 500;
}
::v-deep .ag-theme-alpine-dark .ag-cell {
  font-size: 13px;
  line-height: 30px;
}
::v-deep .ag-theme-alpine-dark .ag-cell-inline-editing {
  height: 30px;
}
::v-deep .ag-theme-alpine-dark {
  --ag-foreground-color:#dcdcdc;
  --ag-header-background-color:#272727;
  --ag-background-color:#2c2c2c;
  --ag-odd-row-background-color:#303030;
  --ag-border-color:#424242;
}
::v-deep .ag-cell-normal {
  color: #dcdcdc;
}
::v-deep .ag-cell-null {
  color: gray;
}
</style>

<script>
import axios from 'axios'

import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import * as ace from 'ace-builds';
import 'ace-builds/webpack-resolver';
import 'ace-builds/src-noconflict/ext-language_tools';

import {AgGridVue} from "ag-grid-vue";

export default {
  data() {
    return {
      // Tabs Header
      tabs: null,
      tabSelected: 'client',

      // Connections
      connections: [],
      currentConn: 0,
      nconn: 0,
      servers: [],

      // Loadings
      loadingServer: false,
      loadingQuery: false,

      // Database Selector
      databaseItems: [],
      database: '',

      // Servers Tree View
      treeviewOpen: [],
      treeviewImg: {
        MySQL: "fas fa-server",
        PostgreSQL: "fas fa-server",
        Table: "fas fa-th",
        View: "fas fa-th-list",
        Trigger: "fas fa-bolt",
        Event: "far fa-clock",
        Function: "fas fa-code-branch",
        Procedure: "fas fa-compress"
      },
      treeviewColor: {
        MySQL: "#F29111",
        PostgreSQL: "",
        Table: "#ec644b",
        View: "#f2d984",
        Trigger: "#59abe3",
        Function: "#2abb9b",
        Procedure: "#bf55ec",
        Event: "#bdc3c7"
      },
      treeview: [],
      treeviewItems: [],
      treeviewSelected: {},
      treeviewMode: 'servers',
      treeviewSearch: '',

      // Menu (right click)
      showMenu: false,
      x: 0,
      y: 0,
      menuItems: ["Rename", "Truncate", "Delete", "Duplicate", "Export"],

      // ACE Editor
      editor: null,
      editorTools: null,
      editorMarkers: [],
      editorCompleters: [],
      editorQuery: '',

      // Results Table Data
      clientHeaders: [],
      clientItems: [],

      // Structure
      tabStructureSelected: 'columns',
      structureOrigin: {},
      structureHeaders: [],
      structureItems: [],

      // Content
      contentTableSelected: '',
      contentColumnsName: [],
      contentColumnsDefault: [],
      contentPks: [],
      contentSearchColumn: '',
      contentSearchFilterItems: ['=','!=','>','<','>=','<=','LIKE','NOT LIKE','IN','NOT IN','BETWEEN','IS NULL','IS NOT NULL'],
      contentSearchFilter: '=',
      contentSearchFilterText: '',
      contentSearchFilterText2: '', // contentSearchFilterItems == 'BETWEEN'
      contentHeaders: [],
      contentItems: [],

      // Info
      infoEditor: null,

      // Bottom Bar
      bottomBarClient: { text: '', status: '', info: '' },
      bottomBarContent: { text: '', status: '', info: '' },

      // AG Grid
      isRowSelected: false,
      currentCellEditMode: 'edit', // edit - new
      currentCellEditNode: {},
      currentCellEditValues: {},

      // Client Dialog
      dialog: false,
      dialogMode: '',
      dialogTitle: '',
      dialogText: '',
      dialogButtonText1: '',
      dialogButtonText2: '',

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(5000),
      snackbarColor: '',
      snackbarText: '',

      // Helpers
      click: undefined,
      gridEditing: false,
    }
  },
  components: { Splitpanes, Pane, AgGridVue },
  created() {
    this.getServers()
  },
  methods: {
    onColumnResized() {
      // if (ev.source == 'sizeColumnsToFit') {

      // }
    },
    clickTab() {
      console.log("STRUCTURE")
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey) && !this.gridEditing) {
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
    initAceClient() {
      // Editor Settings
      this.editor = ace.edit("editor", {
        mode: "ace/mode/sql",
        theme: "ace/theme/monokai",
        fontSize: 14,
        showPrintMargin: false,
        wrap: true,
        autoScrollEditorIntoView: true,
        enableBasicAutocompletion: true,
        enableLiveAutocompletion: true,
        enableSnippets: false,
        highlightActiveLine: false
      });
      this.editor.session.setOptions({ tabSize: 4, useSoftTabs: false })
      this.editorTools = ace.require("ace/ext/language_tools")

      // Highlight Queries
      this.editor.on("changeSelection", this.highlightQueries)

      // Add custom keybinds
      this.editor.commands.removeCommand('transposeletters')
      this.editor.container.addEventListener("keydown", (e) => {
        // if (e.key.toLowerCase() == "w" && (navigator.platform.match("Mac") ? e.metaKey : e.ctrlKey))
        // - New Connection -
        if (e.key.toLowerCase() == "t" && (e.ctrlKey || e.metaKey)) {
          this.newConnection()
          e.preventDefault()
        }
        // - Remove Connection -
        else if (e.key.toLowerCase() == "w" && (e.ctrlKey || e.metaKey)) {
          this.removeConnection(this.currentConn)
          e.preventDefault()
        }
        // - Run Query/ies -
        else if (e.key.toLowerCase() == "r" && (e.ctrlKey || e.metaKey)) {
          if (this.connections.length > 0 && this.editorQuery.length > 0) this.runQuery()
          e.preventDefault()
        }
        // - Increase Font Size -
        else if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
          let size = parseInt(this.editor.getFontSize(), 10) || 12
          this.editor.setFontSize(size + 1)
          e.preventDefault()
        }
        // - Decrease Font Size -
        else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
          let size = parseInt(this.editor.getFontSize(), 10) || 12
          this.editor.setFontSize(Math.max(size - 1 || 1))
          e.preventDefault()
        }
      }, false);

      // Convert Completer Keywords to Uppercase
      const defaultUpperCase = {
        getCompletions(editor, session, pos, prefix, callback) {
          if (session.$mode.completer) {
            return session.$mode.completer.getCompletions(editor, session, pos, prefix, callback);
          }
          const state = editor.session.getState(pos.row);
          let keywordCompletions;
          // if (prefix === prefix.toUpperCase()) {
            keywordCompletions = session.$mode.getCompletions(state, session, pos, prefix);
            keywordCompletions = keywordCompletions.map((obj) => {
              const copy = obj;
              copy.value = obj.value.toUpperCase();
              return copy;
            });
          // } else {
          //   keywordCompletions = session.$mode.getCompletions(state, session, pos, prefix);
          // }
          return callback(null, keywordCompletions);
        },
      };
      this.editor.completers = [defaultUpperCase]

      // Resize after Renderer
      this.editor.renderer.on('afterRender', this.resize);

      // Focus Editor
      this.editor.focus()
    },
    editorAddCompleter(list) {
      const newCompleter = {
        identifierRegexps: [/[^\s]+/],
        getCompletions: function(editor, session, pos, prefix, callback) {
          callback(
            null,
            list.filter(entry => {
              return entry.value.toLowerCase().includes(prefix.toLowerCase())
            }).map(entry => {
              return { 
                value: entry.value,
                meta: entry.meta
              };
            })
          );
        }
      }
      this.editor.completers.push(newCompleter)
      this.editorCompleters.push(newCompleter)
    },
    editorRemoveCompleter(index) {
      this.editor.completers.splice(index+1, 1)
      this.editorCompleters.splice(index, 1)
    },
    check(e) {
      console.log(e)
    },
    highlightQueries() {
      var Range = ace.require("ace/range").Range
      var cursorPosition = this.editor.getCursorPosition()
      var cursorPositionIndex = this.editor.session.doc.positionToIndex(cursorPosition)
      var editorText = this.editor.getValue()

      // Get all Query Positions
      var queries = []
      var start = 0;
      var chars = []
      for (var i = 0; i < editorText.length; ++i) {
        if (editorText[i] == ';' && chars.length == 0) {
          queries.push({"begin": start, "end": i})
          start = i+1
        }
        else if (editorText[i] == "\"") {
          if (chars[chars.length-1] == '"') chars.pop()
          else chars.push("\"")
        }
        else if (editorText[i] == "'") {
          if (chars[chars.length-1] == "'") chars.pop()
          else chars.push("'")
        }
      }
      if (start < i && editorText.substring(start, i).trim().length > 0) queries.push({"begin": start, "end": i})

      // Get Cursor Position Index
      if (queries.length > 0) {
        cursorPositionIndex = (cursorPositionIndex > queries[queries.length-1]['end']) ? queries[queries.length-1]['end'] : cursorPositionIndex 
      }

      // Get Current Query
      var query = ''
      for (let i = 0; i < queries.length; ++i) {
        if (cursorPositionIndex >= queries[i]['begin'] && cursorPositionIndex <= queries[i]['end']) {
          query = editorText.substring(queries[i]['begin'], queries[i]['end'])
          break
        }
      }
      this.editorQuery = query

      // Get Current Query Position
      var queryPosition = 0
      for (let i = 0; i < queries.length; ++i) {
        var re = new RegExp('\\b' + query.trim() + '\\b');
        if (
          re.test(editorText.substring(queries[i]['begin'], queries[i]['end']).trim()) ||
          query.trim().localeCompare(editorText.substring(queries[i]['begin'], queries[i]['end']).trim()) == 0
        ) {
          if (cursorPositionIndex > queries[i]['end']) queryPosition += 1
          else break
        }
      }

      // Find Current Query in Ace Editor
      this.editor.$search.setOptions({
        needle: query.trim(),
        caseSensitive: true,
        wholeWord: true,
        regExp: false,
      }); 
      var queryRange = this.editor.$search.findAll(this.editor.session)

      // Remove Previous Markers
      while (this.editorMarkers.length > 0) {
        this.editor.session.removeMarker(this.editorMarkers.pop())
      }

      // Highlight Current Query
      if (query.trim().length > 0 && queryRange.length > 0) {
        var marker = this.editor.session.addMarker(new Range(queryRange[queryPosition]['start'].row, queryRange[queryPosition]['start'].column, queryRange[queryPosition]['end'].row, queryRange[queryPosition]['end'].column), 'ace_active-line', true)
        this.editorMarkers.push(marker)
      }
    },
    treeviewClick(item) {
      return new Promise ((resolve) => {
        if (this.click) {
          clearTimeout(this.click)
          resolve('double')
        }
        this.click = setTimeout(() => {
          this.click = undefined          
          resolve('single')
        }, 200)
      }).then((data) => {
        // Single Click
        if (data == 'single') {
          if (item.children === undefined) {
            if (this.treeviewSelected == item) {
              this.treeviewSelected = {}
              this.tabClient()
            }
            else {
              this.treeviewSelected = item
              if (this.tabSelected == 'content') this.getContent()
            }
          }
        }
        // Double Click
        else if (data == 'double') {
          if (this.treeviewMode == 'servers') this.getDatabases(item)
          else if (this.treeviewMode == 'objects' && ['Table','View'].includes(item.type) && item.children === undefined) {
            this.treeview = []
            this.treeviewSelected = item
            this.tabs = 2
            this.tabSelected = 'content'
            this.getContent()
          }
        }
      })
    },
    getServers() {
      axios.get('/client/servers')
        .then((response) => {
          this.parseServers(response.data.data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    parseServers(data) {
      var servers = []
      for (let i = 0; i < data.length; ++i) {
        let found = false
        for (var j = 0; j < servers.length; ++j) {
          if (servers[j]['id'] == 'r' + data[i]['region_id']) {
            found = true
            break
          }
        }
        if (found) servers[j]['children'].push({ id: data[i]['server_id'], name: data[i]['server_name'], type: data[i]['server_engine'], host: data[i]['server_hostname'] })
        else servers.push({ id: 'r' + data[i]['region_id'], name: data[i]['region_name'], children: [{ id: data[i]['server_id'], name: data[i]['server_name'], type: data[i]['server_engine'], host: data[i]['server_hostname'] }] })
      }
      this.treeviewItems = servers.slice(0)
      this.servers = servers.slice(0)
    },
    getDatabases(server) {
      // Select Server
      this.treeview = [server.id]
      this.loadingServer = true
      this.serverSelected = server

      // Retrieve Databases
      axios.get('/client/databases', { params: { server_id: server.id } })
        .then((response) => {
          this.parseDatabases(server, response.data.data)
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loadingServer = false
        })
    },
    parseDatabases(server, data) {
      this.treeview = []
      this.treeviewItems = []
      this.treeviewMode = 'objects'
      this.databaseItems = data
      const connection = { server: server, databases: data }
      if (this.connections.length == 0) this.connections.push(connection)
      else this.connections[this.currentConn] = connection
      this.editor.focus()

      // Clean Treeview Search
      this.treeviewSearch = ''

      // Add database names to the editor autocompleter
      var completer = []
      for (let i = 0; i < data.length; ++i) completer.push({ value: data[i], meta: 'database' })
      this.editorAddCompleter(completer)
    },
    getObjects(database) {
      // Retrieve Tables
      axios.get('/client/objects', { params: { server_id: this.serverSelected.id, database_name: database } })
        .then((response) => {
          this.parseObjects(response.data)
          this.editor.focus()
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
    },
    parseObjects(data) {
      // Build routines
      var procedures = []
      var functions = []
      for (let i = 0; i < data.routines.length; ++i) {
        if (data.routines[i]['type'].toLowerCase() == 'procedure') procedures.push(data.routines[i])
        else functions.push(data.routines[i])
      }
      // Build tables / views
      var tables = []
      var views = []
      for (let i = 0; i < data.tables.length; ++i) {
        if (data.tables[i]['type'].toLowerCase() == 'table') tables.push(data.tables[i])
        else views.push(data.tables[i])
      }
      // Build objects
      var objects = [
        { id: 'tables', 'name': 'Tables (' + tables.length + ')', type: 'Table', children: [] },
        { id: 'views', 'name': 'Views (' + views.length + ')',  type: 'View', children: [] },
        { id: 'triggers', 'name': 'Triggers (' + data.triggers.length + ')', type: 'Trigger', children: [] },
        { id: 'functions', 'name': 'Functions (' + functions.length + ')',  type: 'Function', children: [] },
        { id: 'procedures', 'name': 'Procedures (' + procedures.length + ')', type: 'Procedure', children: [] },
        { id: 'events', 'name': 'Events (' + data.events.length + ')',  type: 'Event', children: [] }
      ]
      // Parse Tables
      for (let i = 0; i < tables.length; ++i) {
        objects[0]['children'].push({ id: 'table|' + tables[i]['name'], ...tables[i], type: 'Table' })
      }
      // Parse Views
      for (let i = 0; i < views.length; ++i) {
        objects[1]['children'].push({ id: 'view|' + views[i]['name'], ...views[i], type: 'View' })
      }
      // Parse Triggers
      for (let i = 0; i < data.triggers.length; ++i) {
        objects[2]['children'].push({ id: 'trigger|' + data.triggers[i]['name'], ...data.triggers[i], type: 'Trigger' })
      }
      // Parse Functions
      for (let i = 0; i < functions.length; ++i) {
        objects[3]['children'].push({ id: 'function|' + functions[i]['name'], ...functions[i], type: 'Function' })
      }
      // Parse Procedures
      for (let i = 0; i < procedures.length; ++i) {
        objects[4]['children'].push({ id: 'procedure|' + procedures[i]['name'], ...procedures[i], type: 'Procedure' })
      }
      // Parse Events
      for (let i = 0; i < data.events.length; ++i) {
        objects[5]['children'].push({ id: 'event|' + data.events[i]['name'], ...data.events[i], type: 'Event' })
      }
      this.treeviewItems = objects

      // Add table / view names to the editor autocompleter
      var completer = []
      for (let i = 0; i < data.tables.length; ++i) completer.push({ value: data.tables[i]['name'], meta: data.tables[i]['type'] })
      for (let i = 0; i < data.columns.length; ++i) completer.push({ value: data.columns[i]['name'], meta: 'column' })
      if (this.editorCompleters.length > 1) this.editorRemoveCompleter(1)
      this.editorAddCompleter(completer)
    },
    newConnection() {
      if (this.connections.length == 0) return

      // Store connection
      this.__storeConn(this.currentConn)

      // Add new connection
      this.nconn += 1
      var newConn = {
        server: { name: 'Connection ' + this.nconn },
        databases: [],
        database: '',
        treeview: [],
        treeviewItems: this.servers.slice(0),
        treeviewMode: 'servers',
        treeviewSearch: '',
        editor: '',
        editorCompleters: [],
        clientHeaders: [],
        clientItems: [],
        bottomBarClient: { text: '', status: '', info: '' },
        bottomBarContent: { text: '', status: '', info: '' }
      }
      this.connections.push(newConn)
      this.currentConn = this.connections.length - 1
      this.__loadConn(this.currentConn)
    },
    removeConnection(index) {
      if (this.connections.length == 0) return
      this.connections.splice(index, 1)
      if (this.connections.length == 0) {
        this.databaseItems = []
        this.database = ''
        this.treeview = []
        this.treeviewItems = this.servers.slice(0)
        this.treeviewMode = 'servers'
        this.treeviewSearch = ''
        this.editor.setValue('')
        this.editorCompleters = []
        for (let i = 1; i < this.editor.completers.length; ++i) this.editor.completers.splice(i, 1)
        this.clientHeaders = []
        this.clientItems = []
        this.bottomBarClient = { text: '', status: '', info: '' }
        this.bottomBarContent = { text: '', status: '', info: '' }
      }
      else if (index == this.currentConn) {
        if (this.connections.length > index) this.__loadConn(index)
        else this.__loadConn(index-1)
      }
      else if (this.currentConn > index) this.currentConn = index + 1
    },
    changeConnection(index) {
      if (this.currentConn != index) {
        const currentConn = this.currentConn
        setTimeout(() => { 
          // Store connection
          this.__storeConn(currentConn)

          // Load connection
          this.__loadConn(index)
        }, 1);
        // Change connection
        this.currentConn = index
      }
    },
    __storeConn(index) {
      // Store Connection
      this.connections[index] = {
        server: JSON.parse(JSON.stringify(this.connections[index]['server'])),
        databases: this.databaseItems.slice(0),
        database: this.database,
        treeview: this.treeview.slice(0),
        treeviewItems: this.treeviewItems.slice(0),
        treeviewMode: this.treeviewMode,
        treeviewSearch: this.treeviewSearch,
        editor: this.editor.getValue(),
        editorCompleters: this.editorCompleters.slice(0),
        clientHeaders: this.clientHeaders.slice(0),
        clientItems: this.clientItems.slice(0),
        bottomBarClient: JSON.parse(JSON.stringify(this.bottomBarClient)),
        bottomBarContent: JSON.parse(JSON.stringify(this.bottomBarStatus))
      }
    },
    __loadConn(index) {
      this.databaseItems = this.connections[index]['databases'].slice(0)
      this.database = this.connections[index]['database']
      this.treeview = this.connections[index]['treeview'].slice(0)
      this.treeviewItems = this.connections[index]['treeviewItems'].slice(0)
      this.treeviewMode = this.connections[index]['treeviewMode']
      this.treeviewSearch = this.connections[index]['treeviewSearch']
      this.editor.setValue(this.connections[index]['editor'])
      for (let i = 0; i < this.editor.completers.length; ++i) this.editor.completers.splice(1, 1)
      this.editorCompleters =  this.connections[index]['editorCompleters'].slice(0)
      for (let i = 0; i < this.editorCompleters.length; ++i) this.editor.completers.push(this.editorCompleters[i])
      this.clientHeaders = this.connections[index]['clientHeaders'].slice(0)
      this.clientItems = this.connections[index]['clientItems'].slice(0)
      this.bottomBarClient = this.connections[index]['bottomBarClient']
      this.bottomBarContent = this.connections[index]['bottomBarContent']
    },
    runQuery() {
      this.clientHeaders = []
      this.clientItems = []
      this.bottomBarClient = { text: '', status: '', info: '' }
      this.loadingQuery = true
      const payload = {
        server: this.serverSelected.id,
        database: this.database,
        queries: this.__parseQueries()
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          this.parseExecution(JSON.parse(response.data.data))
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else {
            // Get Response Data
            let data = JSON.parse(error.response.data.data)
            this.parseClientBottomBar(data)
            // Close Editor Completer
            this.editor.blur()
            // Show confirmation dialog
            var dialogOptions = {
              'mode': 'queryError',
              'title': 'Error Message',
              'text': data[data.length-1]['error'],
              'button1': 'Close',
              'button2': ''
            }
            this.showDialog(dialogOptions['mode'], dialogOptions['title'], dialogOptions['text'], dialogOptions['button1'], dialogOptions['button2'])
          }
        })
        .finally(() => {
          this.loadingQuery = false
        })
    },
    parseExecution(data) {
      // Build Data Table
      var headers = []
      var items = data[data.length - 1]['data']
      // Build Headers
      if (data.length > 0 && data[0]['data'].length > 0) {
        var keys = Object.keys(data[data.length - 1]['data'][0])
        for (let i = 0; i < keys.length; ++i) {
          let field = keys[i].trim()
          headers.push({ headerName: keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: true })
        }
      }
      this.clientHeaders = headers
      this.clientItems = items
      // Build BottomBar
      this.parseClientBottomBar(data)
    },
    parseClientBottomBar(data) {
      var elapsed = null
      if (data[data.length-1]['time'] !== undefined) {
        elapsed = 0
        for (let i = 0; i < data.length; ++i) {
          elapsed += parseFloat(data[i]['time'])
        }
        elapsed /= data.length
      }
      this.bottomBarClient['status'] = data[data.length-1]['error'] === undefined ? 'success' : 'failure'
      this.bottomBarClient['text'] = data[data.length-1]['query'].endsWith(';') ? data[data.length-1]['query'] : data[data.length-1]['query'] + ';'
      this.bottomBarClient['info'] = (data[data.length-1]['data'] !== undefined && data[data.length-1]['query'].toLowerCase().startsWith('select')) ? data[data.length-1]['data'].length + ' records | ' : ''
      this.bottomBarClient['info'] += data.length + ' queries'
      if (elapsed != null) this.bottomBarClient['info'] += ' | ' + elapsed.toString() + 's elapsed'
    },
    parseContentBottomBar(data) {     
      var elapsed = null
      if (data[data.length-1]['time'] !== undefined) {
        elapsed = 0
        for (let i = 0; i < data.length; ++i) {
          elapsed += parseFloat(data[i]['time'])
        }
        elapsed /= data.length
      }
      this.bottomBarContent['status'] = data[0]['error'] === undefined ? 'success' : 'failure'
      this.bottomBarContent['text'] = data[0]['query']
      this.bottomBarContent['info'] = this.gridApi.getDisplayedRowCount() + ' records'
      if (elapsed != null) this.bottomBarContent['info'] += ' | ' + elapsed.toString() + 's elapsed'
    },
    getContent() {
      this.contentItems = []
      this.contentHeaders = []
      this.contentTableSelected = this.treeviewSelected['name']
      this.bottomBarContent = { status: '', text: '', info: '' }
      const payload = {
        server: this.serverSelected.id,
        database: this.database,
        table: this.treeviewSelected['name'],
        queries: ['SELECT * FROM ' + this.treeviewSelected['name'] + ' LIMIT 1000;' ]
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          this.parseContentExecution(JSON.parse(response.data.data))
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
    },
    parseContentExecution(data) {
      // Build Data Table
      var headers = []
      var items = data[0]['data']
      // Build Headers
      if (data.length > 0) {
        this.contentColumnsName = data[0]['columns']['name']
        this.contentColumnsDefault = data[0]['columns']['default']
        this.contentPks = data[0]['pks']
        this.contentSearchColumn = this.contentColumnsName[0].trim()
        for (let i = 0; i < this.contentColumnsName.length; ++i) {
          let field = this.contentColumnsName[i].trim()
          headers.push({ headerName: this.contentColumnsName[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: true, 
            valueGetter: function(params) {
              return (params.data[field] == null) ? 'NULL' : params.data[field]
            },
            cellClassRules: {
              'ag-cell-null': params => {
                return params.data[field] == null
              },
              'ag-cell-normal': function(params) {
                return params.data[field] != null
              }
            }
          })
        }
      }
      this.contentHeaders = []
      this.contentHeaders = headers
      this.contentItems = items
      this.gridApi.setRowData(items)
      this.isRowSelected = false

      // Build BottomBar
      this.parseContentBottomBar(data)
    },
    getInfo() {
      const payload = {
        server: this.serverSelected.id,
        database: this.database,
        table: this.treeviewSelected['name']
      }
      axios.get('/client/info', { params: payload })
        .then((response) => {
          let data = JSON.parse(response.data.table_syntax)
          this.infoEditor.setValue(data, -1)
          this.infoEditor.focus()
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
    },
    filterClick() {
      // Build query condition
      var condition = ''
      if (this.contentSearchFilter == 'BETWEEN') {
        if (this.contentSearchFilterText.length != 0 && this.contentSearchFilterText2.length != 0) condition = ' WHERE ' + this.contentSearchColumn + " BETWEEN '" + this.contentSearchFilterText + "' AND '" + this.contentSearchFilterText2 + "'"
      }
      else if (['IS NULL','IS NOT NULL'].includes(this.contentSearchFilter)) {
        condition = ' WHERE ' + this.contentSearchColumn + ' ' + this.contentSearchFilter
      }
      else if (['IN','NOT IN'].includes(this.contentSearchFilter) && this.contentSearchFilterText.length != 0) {
        condition = ' WHERE ' + this.contentSearchColumn + ' ' + this.contentSearchFilter + " ("
        let elements = this.contentSearchFilterText.split(',')
        for (let i = 0; i < elements.length; ++i) condition += "'" + elements[i] + "',"
        condition = condition.substring(0, condition.length - 1) + ")"
      }
      else if (this.contentSearchFilterText.length != 0) condition = ' WHERE ' + this.contentSearchColumn + ' ' + this.contentSearchFilter + " '" + this.contentSearchFilterText + "'"
      // Build payload
      const payload = {
        server: this.serverSelected.id,
        database: this.database,
        table: this.treeviewSelected['name'],
        queries: ['SELECT * FROM ' + this.treeviewSelected['name'] + condition + ' LIMIT 1000;' ]
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          this.parseContentExecution(JSON.parse(response.data.data))
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
    },
    __parseQueries() {
      // Get Query/ies (selected or highlighted)
      const selectedText = this.editor.getSelectedText()
      var queries = []
      if (selectedText.length == 0) queries = [this.editorQuery]
      else {
        // Build multi-queries
        let start = 0;
        let chars = []
        for (var i = 0; i < selectedText.length; ++i) {
          if (selectedText[i] == ';' && chars.length == 0) {
            queries.push(selectedText.substring(start, i+1).trim())
            start = i+1
          }
          else if (selectedText[i] == "\"") {
            if (chars[chars.length-1] == '"') chars.pop()
            else chars.push("\"")
          }
          else if (selectedText[i] == "'") {
            if (chars[chars.length-1] == "'") chars.pop()
            else chars.push("'")
          }
        }
        if (start < i) queries.push(selectedText.substring(start, i).trim())
      }
      // Return parsed queries
      return queries
    },
    // ------------
    // --- TABS ---
    // ------------
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.getAllColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.autoSizeColumns(allColumnIds);
    },
    tabClient() {
      this.tabs = 0
      this.tabSelected = 'client'
      setTimeout(() => { this.editor.focus() }, 100)
    },
    tabStructure() {
      this.tabSelected = 'structure'
      if (this.structureHeaders.length == 0) this.getStructure()
      else this.tabStructureColumns()
    },
    tabStructureColumns() {
      this.tabStructureSelected = 'columns'
      this.structureHeaders = this.structureOrigin['columns']['headers'].slice(0)
      this.structureItems = this.structureOrigin['columns']['items'].slice(0)
      // setTimeout(() => { this.gridApi.sizeColumnsToFit() }, 1);
    },
    tabStructureIndexes() {
      this.tabStructureSelected = 'indexes'
      this.structureHeaders = this.structureOrigin['indexes']['headers'].slice(0)
      this.structureItems = this.structureOrigin['indexes']['items'].slice(0)
      // setTimeout(() => { this.gridApi.sizeColumnsToFit() }, 1);
    },
    tabStructureFK() {
      this.tabStructureSelected = 'fks'
      this.structureHeaders = this.structureOrigin['fks']['headers'].slice(0)
      this.structureItems = this.structureOrigin['fks']['items'].slice(0)
      // setTimeout(() => { this.gridApi.sizeColumnsToFit() }, 1);
    },
    tabStructureTriggers() {
      this.tabStructureSelected = 'triggers'
      this.structureHeaders = this.structureOrigin['triggers']['headers'].slice(0)
      this.structureItems = this.structureOrigin['triggers']['items'].slice(0)
      // setTimeout(() => { this.gridApi.sizeColumnsToFit() }, 1);
    },
    tabContent() {
      this.tabSelected = 'content'
      if (this.contentTableSelected != this.treeviewSelected['name']) this.getContent()
    },
    tabInfo(object) {
      this.tabSelected = object + '_info'
      if (this.infoEditor == null) {
        this.infoEditor = ace.edit("infoEditor", {
          mode: "ace/mode/sql",
          theme: "ace/theme/monokai",
          fontSize: 14,
          showPrintMargin: false,
          wrap: true,
          readOnly: true,
          showLineNumbers: false
        });
      }
      this.getInfo()
    },
    getStructure() {
      // Retrieve Tables
      // this.gridApi.showLoadingOverlay()
      const table = this.treeviewSelected['name']
      axios.get('/client/structure', { params: { server: this.serverSelected.id, database: this.database, table: table } })
        .then((response) => {
          this.parseStructure(response.data)
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
    },
    parseStructure(data) {
      // Parse Columns
      var columns_items = JSON.parse(data.columns)
      var columns_headers = []
      if (columns_items.length > 0) {
        var columns_keys = Object.keys(columns_items[0])
        for (let i = 0; i < columns_keys.length; ++i) {
          let field = columns_keys[i].trim()
          columns_headers.push({ headerName: columns_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: true })
        }
      }
      this.structureOrigin['columns'] = { headers: columns_headers, items: columns_items }
      this.structureHeaders = columns_headers
      this.structureItems = columns_items

      // setTimeout(() => { this.gridApi.sizeColumnsToFit() }, 1);
      // this.gridApi.hideOverlay()

      // show 'no rows' overlay
      // this.gridApi.showNoRowsOverlay()

      // clear all overlays
      // this.gridApi.hideOverlay()

      // Parse Indexes
      var indexes_items = JSON.parse(data.indexes)
      var indexes_headers = []
      if (indexes_items.length > 0) {
        var indexes_keys = Object.keys(indexes_items[0])
        for (let i = 0; i < indexes_keys.length; ++i) {
          let field = indexes_keys[i].trim()
          indexes_headers.push({ headerName: indexes_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: true })
        }
      }
      this.structureOrigin['indexes'] = { headers: indexes_headers, items: indexes_items }

      // Parse Foreign Keys
      var fks_items = JSON.parse(data.fks)
      var fks_headers = []
      if (fks_items.length > 0) {
        var fks_keys = Object.keys(fks_items[0])
        for (let i = 0; i < fks_keys.length; ++i) {
          let field = fks_keys[i].trim()
          fks_headers.push({ headerName: fks_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: true })
        }
      }
      this.structureOrigin['fks'] = { headers: fks_headers, items: fks_items } 

      // Parse Triggers
      var triggers_items = JSON.parse(data.triggers)
      var triggers_headers = []
      if (triggers_items.length > 0) {
        var triggers_keys = Object.keys(triggers_items[0])
        for (let i = 0; i < triggers_keys.length; ++i) {
          let field = triggers_keys[i].trim()
          triggers_headers.push({ headerName: triggers_keys[i], colId: field, field: field, sortable: true, filter: true, resizable: true, editable: true })
        }
      }
      this.structureOrigin['triggers'] = { headers: triggers_headers, items: triggers_items } 
    },
    treeviewKeyDown(event) {
      event.preventDefault()
      console.log("key pressed!")
    },
    resize() {
      // Resize Ace Code Editor
      this.editor.resize();
    },
    clickAction(){
      alert('clicked');
    },
    show(e) {
      e.preventDefault();
      this.showMenu = false;
      this.x = e.clientX;
      this.y = e.clientY;
      this.$nextTick(() => {
        this.showMenu = true;
      });
    },
    addRow() {
      // Clean vars
      this.currentCellEditValues = {}
      this.currentCellEditNode = {}
      this.currentCellEditMode = 'new'

      var newData = {}
      for (let i = 0; i < this.contentColumnsName.length; ++i) {
        newData[this.contentColumnsName[i]] = this.contentColumnsDefault[i]
      }

      var rowCount = this.gridApi.getDisplayedRowCount()
      var nodes = this.gridApi.getSelectedNodes()
      for (let i = 0; i < nodes.length; ++i) nodes[i].setSelected(false)

      this.gridApi.applyTransaction({ add: [newData] })
      this.gridApi.setFocusedCell(rowCount, this.contentColumnsName[0])
      var node = this.gridApi.getDisplayedRowAtIndex(rowCount)
      node.setSelected(true)
      this.gridApi.startEditingCell({
        rowIndex: rowCount,
        colKey: this.contentColumnsName[0]
      });
    },
    removeRow() {
      // Show confirmation dialog
      var dialogOptions = {
        'mode': 'confirm',
        'title': 'Delete rows?',
        'text': 'Are you sure you want to delete the selected ' + this.gridApi.getSelectedNodes().length + ' rows from this table? This action cannot be undone.',
        'button1': 'Cancel',
        'button2': 'Delete'
      }
      this.showDialog(dialogOptions['mode'], dialogOptions['title'], dialogOptions['text'], dialogOptions['button1'], dialogOptions['button2'])
    },
    removeRowSubmit() {
      // Build Pks
      let nodes = this.gridApi.getSelectedNodes()
      let pks = []
      for (let i = 0; i < nodes.length; ++i) {
        let pk = []
        for (let j = 0; j < this.contentPks.length; ++j) {
          pk.push(this.contentPks[j] + " = '" + nodes[i].data[this.contentPks[j]] + "'")
        }
        pks.push('(' + pk.join(' AND ') + ')')
      }
      // Build Query
      var query = 'DELETE FROM ' + this.treeviewSelected['name'] + ' WHERE ' + pks.join(' OR ') + ';'

      // Execute Query
      const payload = {
        server: this.serverSelected.id,
        database: this.database,
        queries: [query]
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          // Remove Frontend Rows
          this.gridApi.applyTransaction({ remove: this.gridApi.getSelectedRows() })
          // Build BottomBar
          this.parseContentBottomBar(JSON.parse(response.data.data))
          // Close Dialog
          this.dialog = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else {
            // Show error
            let data = JSON.parse(error.response.data.data)
            let dialogOptions = {
              'mode': 'info',
              'title': 'Unable to delete row(s)',
              'text': data[0]['error'],
              'button1': 'Close',
              'button2': ''
            }
            this.showDialog(dialogOptions['mode'], dialogOptions['title'], dialogOptions['text'], dialogOptions['button1'], dialogOptions['button2'])
            // Build BottomBar
            this.parseContentBottomBar(data)
          }
        })
    },
    onSelectionChanged() {
      this.isRowSelected = this.gridApi.getSelectedNodes().length > 0
    },
    cellEditingStarted(event, edit) {
      this.gridEditing = true
      if (!edit) return

      if (Object.keys(this.currentCellEditNode).length != 0 && this.currentCellEditNode.rowIndex != event.rowIndex) {
        this.gridApi.stopEditing(true)
        this.gridApi.setFocusedCell(this.currentCellEditNode.rowIndex, this.contentColumnsName[0])
        this.gridApi.clearFocusedCell()
        this.currentCellEditNode.setSelected(true)
        this.cellEditingSubmit(this.currentCellEditMode, this.currentCellEditNode, this.currentCellEditValues)
      }
      if (this.currentCellEditValues[event.colDef.field] === undefined) {
        this.currentCellEditValues[event.colDef.field] = {'old': event.value == 'NULL' ? null : event.value}
      }
      // If the cell includes an special character (\n or \t) or the cell == TEXT, ... then open the extended editor
      // ... 
    },
    cellEditingStopped(event, edit) {
      this.gridEditing = false
      if (!edit) return

      // Store row index & node
      if (Object.keys(this.currentCellEditNode).length == 0) {
        this.currentCellEditNode = this.gridApi.getSelectedNodes()[0]
      }
      // Store new value
      if (event.rowIndex == this.currentCellEditNode.rowIndex) {
        if (event.value == 'NULL') this.currentCellEditNode.setDataValue(event.colDef.field, null)
        if (this.currentCellEditMode == 'edit') this.currentCellEditValues[event.colDef.field]['new'] = event.value == 'NULL' ? null : event.value
      }
      // Check if the row has to be edited
      if (this.gridApi.getEditingCells().length == 0) this.cellEditingSubmit(this.currentCellEditMode, this.currentCellEditNode, this.currentCellEditValues)
    },
    cellEditingSubmit(mode, node, values) {
      var query = ''
      var valuesToUpdate = []
      // NEW
      if (mode == 'new') {
        let keys = Object.keys(node.data)
        for (let i = 0; i < keys.length; ++i) {
          if (node.data[keys[i]] == null) valuesToUpdate.push('NULL')
          else valuesToUpdate.push("'" + node.data[keys[i]] + "'")
        }
        query = "INSERT INTO " + this.treeviewSelected['name'] + ' (' + keys.join() + ") VALUES (" + valuesToUpdate.join() + ");"
      }
      // EDIT
      else if (mode == 'edit') {
        let keys = Object.keys(values)
        for (let i = 0; i < keys.length; ++i) {
          if (values[keys[i]]['old'] != values[keys[i]]['new']) {
            if (values[keys[i]]['new'] == null) valuesToUpdate.push(keys[i] + " = NULL")
            else valuesToUpdate.push(keys[i] + " = '" + values[keys[i]]['new'] + "'")
          }
        }
        let pks = []
        for (let i = 0; i < this.contentPks.length; ++i) pks.push(this.contentPks[i] + " = '" + values[this.contentPks[i]]['old'] + "'")
        query = "UPDATE " + this.treeviewSelected['name'] + " SET " + valuesToUpdate.join(', ') + " WHERE " + pks.join(' AND ') + ';'
      }
      if (mode == 'new' || (mode == 'edit' && valuesToUpdate.length > 0)) {
        // Clean vars
        this.currentCellEditMode = 'edit'
        this.currentCellEditNode = {}
        this.currentCellEditValues = {}
        // Execute Query
        const payload = {
          server: this.serverSelected.id,
          database: this.database,
          queries: [query]
        }
        axios.post('/client/execute', payload)
          .then((response) => {
            let data = JSON.parse(response.data.data)
            // Build BottomBar
            this.parseContentBottomBar(data)
            // Check AUTO_INCREMENTs
            if (data[0].query.startsWith('INSERT')) node.setDataValue(this.contentPks[0], data[0].lastRowId)
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else {
              // Show error
              let data = JSON.parse(error.response.data.data)
              let dialogOptions = {
                'mode': 'error',
                'title': 'Unable to write row',
                'text': data[0]['error'],
                'button1': 'Edit row',
                'button2': 'Discard changes'
              }
              this.showDialog(dialogOptions['mode'], dialogOptions['title'], dialogOptions['text'], dialogOptions['button1'], dialogOptions['button2'])
              // Build BottomBar
              this.parseContentBottomBar(data)
              // Restore vars
              this.currentCellEditMode = mode
              this.currentCellEditNode = node
              this.currentCellEditValues = values
            }
          })
      }
    },
    cellEditingDiscard() {
      // Close Dialog
      this.dialog = false

      // Restore old values
      // if (this.currentCellEditMode == 'new') {
      //   this.contentItems.splice(this.currentCellEditNode.rowIndex, 1)
      // }
      // else if (this.currentCellEditMode == 'edit') {
      //   let keys = Object.keys(this.currentCellEditValues)
      //   var newData = this.currentCellEditNode.data
      //   for (let i = 0; i < keys.length; ++i) {
      //     if (this.currentCellEditValues[keys[i]]['old'] != this.currentCellEditValues[keys[i]]['new']) newData[keys[i]] = this.currentCellEditValues[keys[i]]['old']
      //   }
      //   this.currentCellEditNode.setData(newData)
      //   this.currentCellEditNode.setSelected(true)
      // }

      // Clean vars
      this.currentCellEditMode = 'edit'
      this.currentCellEditNode = {}
      this.currentCellEditValues = {}

      this.filterClick()
    },
    cellEditingEdit() {
      // Close Dialog
      this.dialog = false

      // Edit Row
      setTimeout(() => {
        let focused = this.gridApi.getFocusedCell()
        this.currentCellEditNode.setSelected(true)
        this.gridApi.setFocusedCell(focused.rowIndex, focused.column.colId)
        this.gridApi.startEditingCell({
          rowIndex: focused.rowIndex,
          colKey: focused.column.colId
        });
      }, 100);
    },
    showDialog(mode, title, text, button1, button2) {
      this.dialogMode = mode
      this.dialogTitle = title
      this.dialogText = text
      this.dialogButtonText1 = button1
      this.dialogButtonText2 = button2
      this.dialog = true
    },
    dialogSubmit(button) {
      if (this.dialogMode == 'error') {
        if (button == 1) this.cellEditingEdit()
        else if (button == 2) this.cellEditingDiscard()
      }
      else if (this.dialogMode == 'confirm') {
        if (button == 1) this.dialog = false
        else if (button == 2) this.removeRowSubmit()
      }
      else if (this.dialogMode == 'info') {
        this.dialog = false
      }
      else if (this.dialogMode == 'queryError') {
        this.dialog = false
        this.editor.focus()
      }
    },
    notification(message, color, timeout=5) {
      this.snackbarText = message
      this.snackbarColor = color
      this.snackbarTimeout = Number(timeout*1000)
      this.snackbar = true
    }
  }
}
</script>