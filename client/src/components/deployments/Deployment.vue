<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">INFORMATION</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn v-if="'status' in deployment" text title="Show Execution Parameters" @click="parameters()"><v-icon small style="margin-right:10px">fas fa-cog</v-icon>PARAMETERS</v-btn>
          <v-btn v-if="'status' in deployment" text title="Select Execution" @click="select()"><v-icon small style="margin-right:10px">fas fa-mouse-pointer</v-icon>EXECUTIONS</v-btn>
          <v-btn v-if="'status' in deployment" :disabled="['STARTING','IN PROGRESS','STOPPING','QUEUED'].includes(deployment['status'])" text :title="(deployment['status'] == 'CREATED' || deployment['status'] == 'SCHEDULED') ? 'Edit Execution' : 'Re-Deploy Execution'" @click="edit()"><v-icon small style="margin-right:10px">fas fa-meteor</v-icon>{{(deployment['status'] == 'CREATED' || deployment['status'] == 'SCHEDULED') ? 'EDIT' : 'RE-DEPLOY'}}</v-btn>
          <v-divider v-if="['CREATED','SCHEDULED','QUEUED','STARTING','IN PROGRESS','STOPPING'].includes(deployment['status'])" class="mx-3" inset vertical></v-divider>
          <v-btn :disabled="start_execution" v-if="['CREATED','SCHEDULED'].includes(deployment['status'])" text title="Start Execution" @click="start()"><v-icon small style="margin-right:10px">fas fa-play</v-icon>START</v-btn>
          <v-btn v-if="['QUEUED','STARTING','IN PROGRESS','STOPPING'].includes(deployment['status'])" :disabled="deployment['status'] == 'STARTING' || (deployment['status'] == 'STOPPING' && deployment['stopped'] == 'forceful')" text title="Stop Execution" @click="stop()"><v-icon small style="margin-right:10px">fas fa-ban</v-icon>STOP</v-btn>
        </v-toolbar-items>
        <v-divider v-if="'status' in deployment" class="mx-3" inset vertical></v-divider>
        
        <div v-if="(stop_execution && deployment['status'] != 'STOPPED') || deployment['status'] == 'STOPPING'" class="subtitle-1" style="margin-left:5px;">Stopping the execution...</div>
        <div v-else-if="(start_execution && deployment['status'] == 'IN PROGRESS') || deployment['status'] == 'IN PROGRESS'" class="subtitle-1" style="margin-left:5px;">Execution in progress...</div>
        <div v-else-if="deployment['status'] == 'QUEUED'" class="subtitle-1" style="margin-left:5px;">Queue Position: <b>{{ information_items[0]['queue'] }}</b></div>
        <div v-else-if="start_execution || deployment['status'] == 'STARTING'" class="subtitle-1" style="margin-left:5px;">Starting the execution...</div>
        <v-progress-circular v-if="start_execution || (stop_execution && deployment['status'] != 'STOPPED') || deployment['status'] == 'QUEUED' || deployment['status'] == 'STARTING' || deployment['status'] == 'STOPPING' ||  deployment['status'] == 'IN PROGRESS'" :size="22" indeterminate color="white" width="2" style="margin-left:20px; margin-right:10px;"></v-progress-circular>

        <v-chip v-if="deployment['status'] == 'SUCCESS'" label color="#00b16a" style="font-weight:500; margin-left:5px; margin-right:5px;" title="The execution finished successfully">SUCCESS</v-chip>
        <v-chip v-else-if="deployment['status'] == 'WARNING'" label color="#ff9800" style="font-weight:500; margin-left:5px; margin-right:5px;" title="Some queries failed">WARNING</v-chip>
        <v-chip v-else-if="deployment['status'] == 'FAILED'" label color="#EF5354" style="font-weight:500; margin-left:5px; margin-right:5px;" title="An error has occurred during the execution">FAILED</v-chip>
        <v-chip v-else-if="deployment['status'] == 'STOPPED'" label color="#EF5354" style="font-weight:500; margin-left:5px; margin-right:5px;" title="The execution has been interrupted">STOPPED</v-chip>
        <v-divider v-if="['SUCCESS','WARNING','FAILED','STOPPED'].includes(deployment['status'])" class="mx-3" inset vertical></v-divider>

        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn v-if="show_results" text title="Show Execution Progress" @click="show_results = false"><v-icon small style="margin-right:10px;">fas fa-spinner</v-icon>PROGRESS</v-btn>
          <v-btn v-if="show_results" text title="Share Results" @click="shareResults_dialog = true"><v-icon small style="margin-right:10px;">fas fa-share</v-icon>SHARE</v-btn>
          <v-btn v-else-if="deployment['method'] != 'validate' && (deployment['status'] == 'SUCCESS' || deployment['status'] == 'WARNING' || (deployment['status'] == 'FAILED' && !validation_error) || (deployment['status'] == 'STOPPED' && deployment['uri'] != null)) && ('progress' in deployment && 'queries' in deployment['progress'] && 'total' in deployment['progress']['queries'] && deployment['progress']['queries']['total'] > 0)" text title="Show Execution Results" @click="showResults()"><v-icon small style="margin-right:10px;">fas fa-bars</v-icon>RESULTS</v-btn>
        </v-toolbar-items>

        <v-spacer></v-spacer>
        <div v-if="last_updated != ''" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(last_updated) }}</b></div>
        <v-divider class="ml-3 mr-1" inset vertical></v-divider>
        <v-btn icon @click="goBack()"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>

      <!-- RESULTS -->
      <v-card-text v-if="show_results" style="padding:0px; background-color:rgb(55, 53, 64); height:calc(100vh - 180px)">
        <Viewer :src="deployment['uri']" :height="`calc(100vh - 181px)`"></Viewer>
      </v-card-text>

      <v-card-text v-else>
        <!-- INFORMATION -->
        <v-card>
          <v-data-table :headers="information_headers" :items="information_items" hide-default-footer class="elevation-1">
            <template v-slot:[`item.environment`]="{ item }">
              {{ item.environment.name }}
            </template>
            <template v-slot:[`item.mode`]="{ item }">
              <v-icon small :title="item.mode.charAt(0).toUpperCase() + item.mode.slice(1).toLowerCase()" :color="getModeColor(item.mode)" :style="`text-transform:capitalize; margin-left:${item.mode == 'BASIC' ? '8px' : '6px'}`">{{ item.mode == 'BASIC' ? 'fas fa-chess-knight' : 'fas fa-chess-queen' }}</v-icon>
            </template>
            <template v-slot:[`item.method`]="{ item }">
              <span :style="'color: ' + getMethodColor(item.method.toUpperCase())">{{ item.method.toUpperCase() }}</span>
            </template>
            <template v-slot:[`item.status`]="{ item }">
              <v-icon v-if="item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
              <v-icon v-else-if="item.status == 'SCHEDULED'" title="Scheduled" small style="color: #ff9800; margin-left:8px;">fas fa-clock</v-icon>
              <v-icon v-else-if="item.status == 'QUEUED'" :title="`${'Queued: ' + item.queue}`" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
              <v-icon v-else-if="item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
              <v-icon v-else-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
              <v-icon v-else-if="item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
              <v-icon v-else-if="item.status == 'WARNING'" title="Some queries failed" small style="color: #ff9800; margin-left:9px;">fas fa-check</v-icon>
              <v-icon v-else-if="item.status == 'FAILED'" title="Failed" small style="color: #EF5354; margin-left:11px;">fas fa-times</v-icon>
              <v-icon v-else-if="item.status == 'STOPPING'" title="Stopping" small style="color: #ff9800; margin-left:8px;">fas fa-ban</v-icon>
              <v-icon v-else-if="item.status == 'STOPPED'" title="Stopped" small style="color: #EF5354; margin-left:8px;">fas fa-ban</v-icon>
            </template>
            <template v-slot:[`item.created`]="{ item }">
              <span>{{ dateFormat(item.created) }}</span>
            </template>
            <template v-slot:[`item.scheduled`]="{ item }">
              <span>{{ item.scheduled === null ? '' : dateFormat(item.scheduled).slice(0,-3) }}</span>
            </template>
            <template v-slot:[`item.started`]="{ item }">
              <span>{{ dateFormat(item.started) }}</span>
            </template>
            <template v-slot:[`item.ended`]="{ item }">
              <span>{{ dateFormat(item.ended) }}</span>
            </template>
          </v-data-table>
        </v-card>

        <!-- QUERY SYNTAX - ERROR -->
        <div v-if="deployment['progress'] !== undefined && 'syntax' in deployment['progress']" class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">ERROR</div>
        <v-card v-if="deployment['progress'] !== undefined && 'syntax' in deployment['progress']" style="margin-top:15px; margin-left:5px; margin-right:5px;">
          <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
            <v-toolbar-title class="subtitle-1 white--text">QUERIES NOT VALID</v-toolbar-title>
          </v-toolbar>
          <v-card-text style="padding:0px;">
            <v-container style="padding:0px!important; margin:0px!important; max-width: 10000px;">
              <v-layout wrap>
                <v-flex xs12>
                  <div v-for="(query, index) in deployment['progress']['syntax']" :key="query">
                    <div style="padding:15px;" class="body-1 font-weight-regular">{{ query }}</div>
                    <v-divider v-if="index != deployment['progress']['syntax'].length - 1"></v-divider>
                  </div>
                </v-flex>
              </v-layout>
            </v-container>
          </v-card-text>
        </v-card>

        <!-- VALIDATION -->
        <div v-if="validation_data.length > 0 && Object.keys(validation_data[0]).length != 0" class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">VALIDATION</div>
        <!-- validation -->
        <v-card v-if="validation_data.length > 0 && Object.keys(validation_data[0]).length != 0" style="margin-top:15px;">
          <v-data-table :headers="validation_headers" :items="validation_data" hide-default-footer>
            <template v-slot:item="">
              <tr>
                <td v-for="item in Object.keys(validation_data[0])" :key="item">
                  <span v-if="validation_data[0][item] == 'VALIDATING'" class="warning--text"><v-icon small color="warning" style="margin-right:10px;">fas fa-spinner</v-icon><b>{{ validation_data[0][item] }}</b></span>
                  <span v-else-if="validation_data[0][item] == 'SUCCEEDED'" style="color:#00b16a;"><v-icon small color="#00b16a" style="margin-right:10px;">fas fa-check</v-icon><b>{{ validation_data[0][item] }}</b></span>
                  <span v-else-if="validation_data[0][item] == 'FAILED'" class="error--text"><v-icon small color="#EF5354" style="margin-right:10px;">fas fa-times</v-icon><b>{{ validation_data[0][item] }}</b></span>
                </td>
              </tr>
            </template>
          </v-data-table>
        </v-card>

        <!-- VALIDATION - ERROR -->
        <div v-if="validation_data.length > 0 && validation_error" class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">ERROR</div>
        <v-card v-if="validation_data.length > 0 && validation_error" style="margin-top:15px;">
          <v-card-text style="padding:10px 15px 10px 17px;">
            <v-container style="padding:0px!important; margin:0px!important;">
              <v-layout wrap>
                <v-flex xs12>
                  <div v-for="region in Object.keys(deployment['progress']['validation'])" :key="region">
                    <div v-if="!deployment['progress']['validation'][region]['success']">
                      <div v-if="'error' in deployment['progress']['validation'][region] || 'errors' in deployment['progress']['validation'][region]" class="subtitle-1 font-weight-medium warning--text">{{ region }}</div>
                      <div v-if="'error' in deployment['progress']['validation'][region]" class="body-1 font-weight-regular">{{ deployment['progress']['validation'][region]['error'] }}</div>
                      <div v-for="item in deployment['progress']['validation'][region]['errors']" :key="item['server']">
                        <div class="body-1 font-weight-regular"><b>- {{ item['server'] }}.</b> {{ item['error'] }} </div>
                      </div>
                    </div>
                  </div>
                </v-flex>
              </v-layout>
            </v-container>
          </v-card-text>
          
        </v-card>

        <!-- EXECUTION -->
        <div v-if="execution_headers.length > 0" class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">EXECUTION</div>
        <v-card v-if="execution_headers.length > 0" style="margin-top:15px;">
          <!-- Overall -->
          <v-data-table :headers="execution_headers" :items="this.index(execution_overall)" hide-default-footer>
            <template v-slot:item="props">
              <tr>
                <td v-for="item in Object.keys(execution_headers)" :key="item" :style="regionColor(props.item.i, execution_overall[props.item.i][item]) + `width: ${100/execution_headers.length}%`">
                  <span><v-icon small style="margin-right:10px;">{{ regionIcon(execution_overall[props.item.i][item]) }}</v-icon><b>{{ execution_overall[props.item.i][item] }}</b></span>
                </td>
             </tr>
            </template>
          </v-data-table>
          <!-- Servers -->
          <v-data-table v-if="execution_progress.length > 0" :headers="execution_headers" :items="this.index(execution_progress)" hide-default-header :hide-default-footer="execution_progress.length < 11">
            <template v-slot:item="props">
              <tr>
                <td v-for="item in Object.keys(execution_headers)" :key="item" :style="`width: ${100/execution_headers.length}%`">
                  <span v-if="item in execution_progress[props.item.i]" :style="serverColor(execution_progress[props.item.i][item]['progress'])"><b>{{ execution_progress[props.item.i][item]['server'] }}</b> {{ execution_progress[props.item.i][item]['progress'] }}</span>
                </td>
             </tr>
            </template>
          </v-data-table>
        </v-card>

        <!-- EXECUTION - ERROR -->
        <div v-if="deployment['progress'] !== undefined && !('syntax' in deployment['progress']) && !validation_error && 'error' in deployment['progress']">
          <div class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">ERROR</div>
          <v-card style="margin-top:15px; margin-left:5px; margin-right:5px;">
            <v-card-text style="padding:0px;">
              <v-container style="padding:0px!important; margin:0px!important;">
                <v-layout wrap>
                  <v-flex xs12 style="padding-left:5px; padding-right:5px;">
                    <v-textarea :value="deployment['progress']['error']" color="#c6c6c6" auto-grow solo flat readonly hide-details rows="1"></v-textarea>
                  </v-flex>
                </v-layout>
              </v-container>
            </v-card-text>
          </v-card>
        </div>

        <!-- After Execution Headers -->
        <v-layout row wrap style="margin:0px;">
          <v-flex v-if="logs_data.length > 0 && tasks_data.length > 0" xs8>
            <div class="title font-weight-regular" style="padding-top:20px; padding-left:1px;">POST EXECUTION</div>
          </v-flex>
          <v-flex v-else-if="(logs_data.length > 0 && tasks_data.length == 0) || (logs_data.length == 0 && tasks_data.length > 0)" xs4>
            <div class="title font-weight-regular" style="padding-top:20px; padding-left:1px;">POST EXECUTION</div>
          </v-flex>
          <v-flex xs4>
            <div v-if="deployment['ended'] !== null && queries_data.length > 0" class="title font-weight-regular" style="padding-top:20px; padding-left:7px;">QUERIES</div>
          </v-flex>
        </v-layout>

        <!-- POST EXECUTION -->
        <v-layout row wrap style="margin-top:15px; margin-left:0px; margin-right:0px; margin-bottom:0px">
          <!-- logs -->
          <v-flex v-if="logs_data.length > 0" xs4 style="padding-right:5px;">
            <v-card>
              <v-data-table :headers="logs_headers" :items="logs_data" hide-default-footer>
                <template v-slot:[`item.message`]="{ item }">
                  <v-icon v-if="item.status == 'progress'" title="In Progress" small style="color: #ff9800; margin-right:10px;">fas fa-spinner</v-icon>
                  <v-icon v-else-if="item.status == 'success'" title="Success" small style="color: #4caf50; margin-right:10px;">fas fa-check</v-icon>
                  <v-icon v-else-if="item.status == 'failed'" title="Failed" small style="color: #EF5354; margin-right:10px;">fas fa-times</v-icon>
                  {{ item.message }}
                </template>
              </v-data-table>
            </v-card>
          </v-flex>
          <!-- remaining-tasks -->
          <v-flex v-if="tasks_data.length > 0" xs4 style="padding-left:5px; padding-right:5px;">
            <v-card>
              <v-data-table :headers="tasks_headers" :items="tasks_data" hide-default-footer>
                <template v-slot:[`item.message`]="{ item }">
                  <v-icon v-if="item.status == 'progress'" title="In Progress" small style="color: #ff9800; margin-right:10px;">fas fa-spinner</v-icon>
                  <v-icon v-else-if="item.status == 'success'" title="Success" small style="color: #4caf50; margin-right:10px;">fas fa-check</v-icon>
                  <v-icon v-else-if="item.status == 'failed'" title="Failed" small style="color: #EF5354; margin-right:10px;">fas fa-times</v-icon>
                  {{ item.message }}
                </template>
              </v-data-table>
            </v-card>
          </v-flex>
          <!-- queries -->
          <v-flex v-if="deployment['ended'] !== null && queries_data.length > 0" xs4 style="padding-left:5px;">
            <v-card>
              <v-data-table :headers="queries_headers" :items="queries_data" hide-default-footer>
                <template v-slot:[`item.succeeded`]="{ item }">
                  <span class="font-weight-medium" style="color: rgb(0, 177, 106)">{{ item.succeeded }}</span>
                </template>
                <template v-slot:[`item.failed`]="{ item }">
                  <span class="font-weight-medium" style="color: #EF5354">{{ item.failed }}</span>
                </template>
                <template v-slot:[`item.rollback`]="{ item }">
                  <span class="font-weight-medium" style="color: rgb(250, 130, 49)">{{ item.rollback }}</span>
                </template>
              </v-data-table>
            </v-card>
          </v-flex>
        </v-layout>
      </v-card-text>
    </v-card>

    <v-dialog v-model="information_dialog" persistent no-click-animation max-width="80%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title v-show="information_dialog_mode == 'parameters'" class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-cog</v-icon>PARAMETERS</v-toolbar-title>
          <v-toolbar-title v-show="information_dialog_mode == 'edit'" class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-meteor</v-icon>EDIT</v-toolbar-title>
          <v-toolbar-title v-show="information_dialog_mode == 're-deploy'" class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-meteor</v-icon>RE-DEPLOY</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="basicClick" :readonly="information_dialog_mode == 'parameters'" :color="information_dialog_execution_mode == 'BASIC' ? 'primary' : '#779ecb'"><v-icon small style="margin-right:10px; margin-bottom:1px">fas fa-chess-knight</v-icon>BASIC</v-btn>
          <v-btn @click="proClick" :readonly="information_dialog_mode == 'parameters'" :color="information_dialog_execution_mode == 'PRO' ? 'primary' : '#779ecb'" style="margin-left:10px"><v-icon small style="margin-right:10px; margin-bottom:1px">fas fa-chess-queen</v-icon>PRO</v-btn>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" icon @click="information_dialog = false"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 15px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form">
                  <v-autocomplete :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.environment" :items="environments" item-value="id" return-object item-text="name" label="Environment" :rules="[v => !!v || '']">
                    <template v-slot:item="{ item }" >
                      <v-row align="center" no-gutters>
                        <v-col class="flex-grow-1 flex-shrink-1">
                          {{ item.name }}
                        </v-col>
                        <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
                          <v-chip label><v-icon small :color="item.shared ? '#EF5354' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>{{ item.shared ? 'Shared' : 'Personal' }}</v-chip>
                        </v-col>
                      </v-row>
                    </template>
                  </v-autocomplete>
                  <v-text-field v-if="information_dialog_execution_mode == 'BASIC'" :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.databases" label="Databases" hint="Separated by commas. Wildcards allowed: % _" :rules="[v => !!v || '']" style="padding-top:0px;"></v-text-field>
                  <v-card v-if="information_dialog_execution_mode == 'BASIC'" style="margin-bottom:20px;">
                    <v-toolbar flat dense color="#2e3131" style="margin-top:5px;">
                      <v-toolbar-title class="white--text subtitle-1">QUERIES</v-toolbar-title>
                      <v-divider v-if="information_dialog_mode != 'parameters'" class="mx-3" inset vertical></v-divider>
                      <v-toolbar-items v-if="information_dialog_mode != 'parameters'" class="hidden-sm-and-down" style="padding-left:0px;">
                        <v-btn text @click='newQuery()'><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                        <v-btn :disabled="information_dialog_query_selected.length != 1" text @click="cloneQuery()"><v-icon small style="margin-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
                        <v-btn :disabled="information_dialog_query_selected.length != 1" text @click="editQuery()"><v-icon small style="margin-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                        <v-btn :disabled="information_dialog_query_selected.length == 0" text @click='deleteQuery()'><v-icon small style="margin-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                        <v-divider class="mx-3" inset vertical></v-divider>
                        <v-btn :disabled="information_dialog_data.queries.length < 2 || information_dialog_query_selected.length != 1" text title="Move query to the top" @click="moveTopQuery()"><v-icon small style="margin-right:10px">fas fa-level-up-alt</v-icon>TOP</v-btn>
                        <v-btn :disabled="information_dialog_data.queries.length < 2 || information_dialog_query_selected.length != 1" text title="Move query up" @click="moveUpQuery()"><v-icon small style="margin-right:10px">fas fa-arrow-up</v-icon>UP</v-btn>
                        <v-btn :disabled="information_dialog_data.queries.length < 2 || information_dialog_query_selected.length != 1" text title="Move query down" @click="moveDownQuery()"><v-icon small style="margin-right:10px">fas fa-arrow-down</v-icon>DOWN</v-btn>
                        <v-btn :disabled="information_dialog_data.queries.length < 2 || information_dialog_query_selected.length != 1" text title="Move query to the bottom" @click="moveBottomQuery()"><v-icon small style="margin-right:10px">fas fa-level-down-alt</v-icon>BOTTOM</v-btn>
                      </v-toolbar-items>
                    </v-toolbar>
                    <v-divider></v-divider>
                    <v-data-table v-model="information_dialog_query_selected" :headers="information_dialog_data.query_headers" :items="information_dialog_data.queries" item-key="id" :show-select="information_dialog_mode != 'parameters'" :hide-default-header="information_dialog_mode == 'parameters'" :hide-default-footer="typeof information_dialog_data.queries === 'undefined' || information_dialog_data.queries.length < 11" class="elevation-1">
                      <template v-ripple v-slot:[`header.data-table-select`]="{}">
                        <v-simple-checkbox
                          :value="information_dialog_data.queries.length == 0 ? false : information_dialog_query_selected.length == information_dialog_data.queries.length"
                          :indeterminate="information_dialog_query_selected.length > 0 && information_dialog_query_selected.length != information_dialog_data.queries.length"
                          @click="information_dialog_query_selected.length == information_dialog_data.queries.length ? information_dialog_query_selected = [] : information_dialog_query_selected = JSON.parse(JSON.stringify(information_dialog_data.queries))">
                        </v-simple-checkbox>
                      </template>
                    </v-data-table>
                  </v-card>
                  <div v-if="information_dialog_execution_mode == 'PRO'" style="margin-top:-5px; margin-bottom:10px;">
                    <v-tooltip right>
                      <template v-slot:activator="{ on }">
                        <span v-on="on" class="subtitle-1 font-weight-regular white--text">
                          CODE
                          <v-icon small style="margin-left:5px; margin-bottom:2px;">fas fa-question-circle</v-icon>
                        </span>
                      </template>
                      <span>Press <span class="font-weight-medium" style="color:rgb(250, 130, 49)">ESC</span> when cursor is in the editor to toggle full screen editing</span>
                    </v-tooltip>
                  </div>
                  <codemirror ref="myCm" v-show="information_dialog_execution_mode == 'PRO'" v-model="information_dialog_data.code" :options="cmOptions" style="margin-bottom:15px;"></codemirror>
                  <div style="margin-top:20px">
                    <v-tooltip right>
                      <template v-slot:activator="{ on }">
                        <span v-on="on" class="subtitle-1 font-weight-regular white--text">
                          METHOD
                          <v-icon small style="margin-left:5px; margin-bottom:2px;" v-on="on">fas fa-question-circle</v-icon>
                        </span>
                      </template>
                      <span>
                        <b style="color:#00b16a">VALIDATE</b> Tests all server connections
                        <br>
                        <b class="orange--text">TEST</b> A simulation is performed (only SELECTs & SHOWs are executed)
                        <br>
                        <b style="color:#EF5354">DEPLOY</b> Executes ALL queries
                      </span>
                    </v-tooltip>
                  </div>
                  <v-radio-group :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.method" hide-details style="margin-top:10px;">
                    <v-radio value="validate" color="#00b16a">
                      <template v-slot:label>
                        <div style="color:#00b16a;">VALIDATE</div>
                      </template>
                    </v-radio>
                    <v-radio value="test" color="orange">
                      <template v-slot:label>
                        <div class="orange--text">TEST</div>
                      </template>
                    </v-radio>
                    <v-radio value="deploy" color="#EF5354">
                      <template v-slot:label>
                        <div style="color:#EF5354">DEPLOY</div>
                      </template>
                    </v-radio>
                  </v-radio-group>
                  <v-switch v-model="schedule_enabled" @change="schedule_change()" label="Scheduled" color="info" hide-details :readonly="information_dialog_mode == 'parameters'"></v-switch>
                  <v-text-field v-if="schedule_enabled && schedule_datetime != ''" solo v-model="schedule_datetime" @click="schedule_change()" title="Click to edit the schedule datetime" hide-details readonly style="margin-top:10px; margin-bottom:10px;"></v-text-field>
                  <v-checkbox v-else-if="information_dialog_mode != 'parameters'" :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.start_execution" label="Start execution" color="primary" hide-details></v-checkbox>
                  <v-divider v-if="information_dialog_mode != 'parameters'" style="margin-top:15px;"></v-divider>
                  <div v-if="information_dialog_mode != 'parameters'" style="margin-top:20px;">
                    <v-btn :loading="loading" color="#00b16a" @click="editSubmit()">{{ information_dialog_mode == 'edit' ? 'CONFIRM' : 'RE-DEPLOY' }}</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="information_dialog = false" style="margin-left:5px">CANCEL</v-btn>
                  </div>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="scheduleDialog" persistent width="290px">
      <v-date-picker v-if="schedule_mode=='date'" v-model="schedule_date" color="info" scrollable>
        <v-btn text color="#00b16a" @click="schedule_submit()">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="schedule_close()">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="schedule_now()">Now</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="schedule_mode=='time'" v-model="schedule_time" color="info" format="24hr" scrollable>
        <v-btn text color="#00b16a" @click="schedule_submit()">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="schedule_close()">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="schedule_now()">Now</v-btn>
      </v-time-picker>
    </v-dialog>

    <v-dialog v-model="query_dialog" eager persistent max-width="896px">
      <v-toolbar flat dense color="primary">
        <v-toolbar-title class="white--text subtitle-1">{{ query_dialog_title }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text style="padding:0px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div v-if="query_dialog_mode == 'delete'" class="subtitle-1" style="margin:15px">Are you sure you want to delete the selected queries?</div>
                <div v-else>
                  <codemirror id="codemirrorQuery" ref="codemirror" v-model="query_dialog_code" :options="cmOptions2"></codemirror>
                </div>
                <v-divider style="margin:15px"></v-divider>
                <div style="padding:0px 15px 15px 15px">
                  <v-btn color="#00b16a" @click="queryActionConfirm()">Confirm</v-btn>
                  <v-btn color="#EF5354" @click="query_dialog=false" style="margin-left:5px">Cancel</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="select_dialog" max-width="90%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-mouse-pointer</v-icon>EXECUTIONS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="select_dialog = false"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 15px 20px 20px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-card>
                  <v-toolbar flat dense color="#2e3131">
                    <v-toolbar-title class="white--text subtitle-2">SELECT EXECUTION</v-toolbar-title>
                  </v-toolbar>
                  <v-divider></v-divider>
                  <v-data-table :headers="executions.headers" :items="executions.items" item-key="id" class="elevation-1">
                    <template v-slot:item="props">
                      <tr :style="`background-color:` + selectRow(props.item.id)">
                        <td>{{ props.item.environment }}</td>
                        <td><v-icon small :title="props.item.mode.charAt(0).toUpperCase() + props.item.mode.slice(1).toLowerCase()" :color="getModeColor(props.item.mode)" :style="`text-transform:capitalize; margin-left:${props.item.mode == 'BASIC' ? '8px' : '6px'}`">{{ props.item.mode == 'BASIC' ? 'fas fa-chess-knight' : 'fas fa-chess-queen' }}</v-icon></td>
                        <td><span :style="'color: ' + getMethodColor(props.item.method.toUpperCase())">{{ props.item.method.toUpperCase() }}</span></td>
                        <td>
                          <v-icon v-if="props.item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
                          <v-icon v-else-if="props.item.status == 'SCHEDULED'" title="Scheduled" small style="color: #ff9800; margin-left:8px;">fas fa-clock</v-icon>
                          <v-icon v-else-if="props.item.status == 'QUEUED'" :title="`${'Queued: ' + props.item.queue}`" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
                          <v-icon v-else-if="props.item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
                          <v-icon v-else-if="props.item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
                          <v-icon v-else-if="props.item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
                          <v-icon v-else-if="props.item.status == 'WARNING'" title="Some queries failed" small style="color: #ff9800; margin-left:9px;">fas fa-check</v-icon>
                          <v-icon v-else-if="props.item.status == 'FAILED'" title="Failed" small style="color: #EF5354; margin-left:11px;">fas fa-times</v-icon>
                          <v-icon v-else-if="props.item.status == 'STOPPING'" title="Stopping" small style="color: #ff9800; margin-left:8px;">fas fa-ban</v-icon>
                          <v-icon v-else-if="props.item.status == 'STOPPED'" title="Stopped" small style="color: #EF5354; margin-left:8px;">fas fa-ban</v-icon>
                        </td>
                        <td>{{ dateFormat(props.item.created) }}</td>
                        <td>{{ dateFormat(props.item.started) }}</td>
                        <td>{{ dateFormat(props.item.ended) }}</td>
                        <td>{{ props.item.overall }}</td>
                        <td>
                          <v-btn icon @click="selectExecution(props.item.id)"><v-icon title="Select execution" small>fas fa-arrow-right</v-icon></v-btn>
                        </td>
                      </tr>
                    </template>
                  </v-data-table>
                </v-card>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="action_dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">{{ action_dialog_title }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div v-if="action_dialog_text.length > 0" class="subtitle-1" style="margin-bottom:10px">{{ action_dialog_text }}</div>
                <div v-if="action_dialog_mode == 'stop'">
                  <div v-if="deployment['status'] == 'QUEUED' || execution_headers.length == 0 || logs_data.length > 0">
                    <div class="subtitle-1" style="margin-top:5px; margin-bottom:10px">Want to stop the execution?</div>
                  </div>
                  <div v-else>
                    <div class="subtitle-1 font-weight-medium">METHOD</div>
                    <v-radio-group v-model="stop_execution_mode" hide-details style="margin-top:10px; margin-bottom:20px;">
                      <v-radio :disabled="deployment['stopped'] != null" label="Graceful - Wait current databases to finish." value="graceful" color="warning"></v-radio>
                      <v-radio label="Forceful - Do not wait current databases to finish and stop ongoing queries." value="forceful" color="#EF5354"></v-radio>
                    </v-radio-group>
                  </div>
                </div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn color="#00b16a" @click="actionSubmit()">Confirm</v-btn>
                  <v-btn color="#EF5354" @click="action_dialog=false" style="margin-left:5px;">Cancel</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="shareResults_dialog" max-width="896px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-share</v-icon>SHARE RESULTS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-toolbar-items class="hidden-sm-and-down">
            <v-btn text :title="shareResults_dialog_title" @click="resultsShare()"><v-icon small style="margin-right:10px">{{ shareResults_dialog_icon }}</v-icon>{{ shareResults_dialog_text }}</v-btn>
            <v-btn text title="Copy link to clipboard" @click="resultsClipboard()"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-copy</v-icon>COPY LINK</v-btn>
          </v-toolbar-items>
          <v-spacer></v-spacer>
          <v-btn icon @click="shareResults_dialog = false"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px">
          <v-container>
            <v-layout wrap>
              <v-flex xs12>
                <v-btn ref="results_url" block text :href="url + `/viewer/` + deployment['uri']" target="_blank" class="font-weight-light text-lowercase" style="font-size:18px; letter-spacing:0.05em">{{url + `/viewer/` + deployment['uri'] }}</v-btn>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<style>
.CodeMirror {
  min-height: 450px;
  font-size: 14px;
}
.CodeMirror pre {
  padding: 0 14px;
}
.CodeMirror-scrollbar-filler {
  background-color: rgb(55, 53, 64);
}
#codemirrorQuery .CodeMirror {
  min-height: 60vh;
}
</style>

<style scoped>
/* .v-data-table
  ::v-deep tr:hover:not(.v-data-table__selected) {
  background: transparent !important;
} */
</style>

<script>
  import axios from 'axios'
  import moment from 'moment'

  // CODE-MIRROR
  import { codemirror } from 'vue-codemirror'
  import 'codemirror/lib/codemirror.css'

  // language
  import 'codemirror/mode/python/python.js'
  import 'codemirror/mode/sql/sql.js'
  // theme css
  import 'codemirror/theme/one-dark.css' // monokai.css

  // require active-line.js
  import 'codemirror/addon/selection/active-line.js'
  // closebrackets
  import 'codemirror/addon/edit/closebrackets.js'
  // keyMap
  import 'codemirror/mode/clike/clike.js'
  import 'codemirror/addon/edit/matchbrackets.js'
  import 'codemirror/addon/comment/comment.js'
  import 'codemirror/addon/dialog/dialog.js'
  import 'codemirror/addon/dialog/dialog.css'
  import 'codemirror/addon/selection/mark-selection.js'
  import 'codemirror/addon/search/searchcursor.js'
  import 'codemirror/addon/search/search.js'
  import 'codemirror/keymap/sublime.js'
  import 'codemirror/addon/selection/active-line.js'
  import 'codemirror/addon/display/fullscreen.js'
  import 'codemirror/addon/display/fullscreen.css'

  // VIEWER
  import Viewer from './Viewer'

  export default  {
    data: () => ({
      // Deployment Data
      deployment: {},

      // Environments
      environments: [],

      // Deployment Executions
      executions: {},

      // Last Updated
      last_updated: '',

      // Information
      information_headers: [
        { text: 'Name', value: 'name', sortable: false },
        { text: 'Release', align: 'left', value: 'release', sortable: false },
        { text: 'Environment', value: 'environment', sortable: false },
        { text: 'Mode', value: 'mode', sortable: false },
        { text: 'Method', value: 'method', sortable: false },
        { text: 'Status', value: 'status', sortable: false },
        { text: 'Created', value: 'created', sortable: false },
        { text: 'Started', value: 'started', sortable: false },
        { text: 'Ended', value: 'ended', sortable: false },
        { text: 'Overall', value: 'overall', sortable: false },
      ],
      information_items: [],

      // Validation
      validation_headers: [],
      validation_data: [],
      validation_error: false,

      // Execution
      execution_headers: [],
      execution_overall: [],
      execution_progress: [],

      // Post Execution
      logs_headers: [{ text: 'LOGS', align:'left', value: 'message', sortable: false }],
      logs_data: [],
      tasks_headers: [{ text: 'REMAINING TASKS', align:'left', value: 'message', sortable: false }],
      tasks_data: [],
      queries_headers: [
        { text: 'TOTAL', align:'left', value: 'total', sortable: false },
        { text: 'SUCCEEDED', align:'left', value: 'succeeded', sortable: false },
        { text: 'FAILED', align:'left', value: 'failed', sortable: false },
        { text: 'ROLLBACK', align:'left', value: 'rollback', sortable: false }
      ],
      queries_data: [],

      // Dialogs
      // - Information -
      information_dialog: false,
      information_dialog_mode: '',
      information_dialog_execution_mode: '',
      information_dialog_data: { queries: [] },
      information_dialog_query_selected: [],
      code: '',
      // - Query -
      query_dialog: false,
      query_dialog_mode: '',
      query_dialog_title: '',
      query_dialog_code: '',
      // - Select -
      select_dialog: false,
      // - Action -
      action_dialog: false,
      action_dialog_title: '',
      action_dialog_text: '',
      action_dialog_mode: '',

      // Schedule
      scheduleDialog: false,
      schedule_enabled: false,
      schedule_mode: 'date',
      schedule_date: '',
      schedule_time: '',
      schedule_datetime: '',

      // Share Results Dialog
      shareResults_dialog: false,
      shareResults_dialog_title: '',
      shareResults_dialog_text: '',
      shareResults_dialog_icon: '',

      // Executions Flag
      stop_execution: false,
      stop_execution_mode: 'graceful',
      start_execution: false,
      show_results: false,

      // Init Code Parameters
      cmOptions: {
        readOnly: true,
        autoRefresh: true,
        autoCloseBrackets: true,
        styleActiveLine: true,
        lineNumbers: true,
        tabSize: 4,
        indentUnit: 4,
        line: true,
        foldGutter: true,
        matchBrackets: true,
        showCursorWhenSelecting: true,
        mode: 'python',
        theme: 'one-dark',
        keyMap: 'sublime',
        extraKeys: {
          Tab: function(cm) {
            if (cm.somethingSelected()) cm.indentSelection("add")
            else cm.replaceSelection("    " , "end")
          },
          "Esc": function(cm) {
            cm.setOption("fullScreen", !cm.getOption("fullScreen"))
          },
          "Ctrl-S": function(cm) {
            var textFileAsBlob = new Blob([cm.getValue()], { type: "text/plain;charset=utf-8" })
            var downloadLink = document.createElement("a")
            downloadLink.download = "meteor.py"
            downloadLink.style.display = "none"
            if (window.webkitURL != null) downloadLink.href = window.webkitURL.createObjectURL(textFileAsBlob)
            else downloadLink.href = window.URL.createObjectURL(textFileAsBlob)
            document.body.appendChild(downloadLink)
            downloadLink.click()
            document.body.removeChild(downloadLink)
          },
          "Cmd-S": function(cm) {
            var textFileAsBlob = new Blob([cm.getValue()], { type: "text/plain;charset=utf-8" })
            var downloadLink = document.createElement("a")
            downloadLink.download = "meteor.py"
            downloadLink.style.display = "none"
            if (window.webkitURL != null) downloadLink.href = window.webkitURL.createObjectURL(textFileAsBlob)
            else downloadLink.href = window.URL.createObjectURL(textFileAsBlob)
            document.body.appendChild(downloadLink)
            downloadLink.click()
            document.body.removeChild(downloadLink)
          }
        }
      },
      cmOptions2: {
        readOnly: false,
        autoCloseBrackets: true,
        styleActiveLine: true,
        lineNumbers: true,
        tabSize: 4,
        indentUnit: 4,
        line: true,
        foldGutter: true,
        matchBrackets: true,
        showCursorWhenSelecting: true,
        mode: 'sql',
        theme: 'one-dark',
        keyMap: 'sublime',
        extraKeys: {
          Tab: function(cm) {
            if (cm.somethingSelected()) cm.indentSelection("add")
            else cm.replaceSelection("    " , "end")
          },
          "Esc": function(cm) {
            cm.setOption("fullScreen", !cm.getOption("fullScreen"))
          },
          "Ctrl-S": function(cm) {
            var textFileAsBlob = new Blob([cm.getValue()], { type: "text/plain;charset=utf-8" })
            var downloadLink = document.createElement("a")
            downloadLink.download = "meteor.py"
            downloadLink.style.display = "none"
            if (window.webkitURL != null) downloadLink.href = window.webkitURL.createObjectURL(textFileAsBlob)
            else downloadLink.href = window.URL.createObjectURL(textFileAsBlob)
            document.body.appendChild(downloadLink)
            downloadLink.click()
            document.body.removeChild(downloadLink)
          },
          "Cmd-S": function(cm) {
            var textFileAsBlob = new Blob([cm.getValue()], { type: "text/plain;charset=utf-8" })
            var downloadLink = document.createElement("a")
            downloadLink.download = "meteor.py"
            downloadLink.style.display = "none"
            if (window.webkitURL != null) downloadLink.href = window.webkitURL.createObjectURL(textFileAsBlob)
            else downloadLink.href = window.URL.createObjectURL(textFileAsBlob)
            document.body.appendChild(downloadLink)
            downloadLink.click()
            document.body.removeChild(downloadLink)
          }
        }
      },
      // Loading
      loading: false,
      timer: null,

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: '',

      // Execution URL
      url: window.location.protocol + '//' + window.location.host,
    }),
    components: { codemirror, Viewer },
    created() {
      this.init()
    },
    mounted() {
      // Check Notification
      setTimeout(this.checkNotifications, 300)
    },
    methods: {
      // -------------
      // BASE METHODS
      // -------------
      init() {
        if (this.$route.params.id === undefined) this.notification('Invalid Deployment Identifier', '#EF5354')
        else {
          this.getDeployment()
          this.getCode()
        }
      },
      goBack() {
        if (this.show_results) this.show_results = false
        else this.$router.back()
      },
      getCode() {
        axios.get('/deployments/blueprint')
          .then((response) => {
            this.code = response.data.data
          })
          .catch((error) => {
            if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
      },
      getDeployment() {
        // Get Deployment Data
        axios.get('/deployments', { params: { id: this.$route.params.id } })
          .then((response) => {
            const data = response.data.deployment
            this.environments = response.data.environments
            this.parseRequest(data)
            if (this.$router.currentRoute.name == 'deployment') {
              if (data['status'] == 'QUEUED' || data['status'] == 'STARTING' || data['status'] == 'STOPPING' || data['status'] == 'IN PROGRESS') {
                clearTimeout(this.timer)
                this.timer = setTimeout(this.getDeployment, 1000)
              }
              else this.start_execution = false
            }
          })
          .catch((error) => {
            if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
      },
      clear() {
        this.information_headers = [
          { text: 'Name', value: 'name', sortable: false },
          { text: 'Release', align: 'left', value: 'release', sortable: false },
          { text: 'Environment', value: 'environment', sortable: false },
          { text: 'Mode', value: 'mode', sortable: false },
          { text: 'Method', value: 'method', sortable: false },
          { text: 'Status', value: 'status', sortable: false },
          { text: 'Created', value: 'created', sortable: false },
          { text: 'Started', value: 'started', sortable: false },
          { text: 'Ended', value: 'ended', sortable: false },
          { text: 'Overall', value: 'overall', sortable: false },
        ]
        this.validation_data = []
        this.execution_headers = []
        this.execution_progress = []
        this.execution_overall = []
        this.logs_data = []
        this.tasks_data = []
        this.queries_data = []
        this.validation_error = false
        this.start_execution = false
        this.stop_execution = false
        if ('progress' in this.deployment && 'syntax' in this.deployment.progress) delete this.deployment.progress.syntax
        if ('progress' in this.deployment && 'error' in this.deployment.progress) delete this.deployment.progress.error
      },
      parseRequest(data) {
        // Parse Deployment Data
        this.deployment['id'] = data['id']
        this.deployment['deployment_id'] = data['deployment_id']
        this.deployment['mode'] = data['mode']
        this.information_dialog_execution_mode = data['mode']
        this.deployment['name'] = data['name']
        this.deployment['release'] = data['release']
        this.deployment['environment'] = { id: data['environment_id'], name: data['environment_name'] }
        this.deployment['query_headers'] = [{text: 'Query', value: 'query'}]
        this.deployment['queries'] = this.deployment['mode'] == 'BASIC' ? JSON.parse(data['queries']) : []
        this.deployment['databases'] = this.deployment['mode'] == 'BASIC' ? data['databases'] : ''
        this.deployment['code'] = this.deployment['mode'] == 'PRO' ? data['code'] : ''
        this.deployment['method'] = data['method'].toLowerCase()
        if (this.deployment['status'] != data['status']) this.getExecutions()
        this.deployment['status'] = data['status']
        this.deployment['stopped'] = data['stopped']
        this.deployment['queue'] = data['queue']
        this.deployment['created'] = data['created']
        this.deployment['scheduled'] = data['scheduled']
        this.deployment['started'] = data['started']
        this.deployment['ended'] = data['ended']
        this.deployment['error'] = data['error']
        this.deployment['uri'] = data['uri']
        this.deployment['url'] = data['url']
        this.deployment['engine'] = data['engine']
        this.deployment['public'] = data['public']
        this.deployment['overall'] = data['overall']

        // Parse Scheduled
        if (this.deployment['scheduled']) {
          const date = moment(this.deployment['scheduled'])
          this.schedule_date = date.format("YYYY-MM-DD")
          this.schedule_time = date.format("HH:mm")
          this.schedule_datetime = date.format("YYYY-MM-DD HH:mm")
          this.schedule_enabled = true
          // Add new 'Scheduled' column if not exist
          var found = false
          for (var h = 0; h < this.information_headers.length; ++h) {
            if (this.information_headers[h]['text'] == 'Scheduled') { found = true; break; }
          }
          if (!found) this.information_headers.splice(7, 0, { text: 'Scheduled', value: 'scheduled', sortable: false })
        }

        // Set Public Values
        this.shareResults_dialog_title = (this.deployment['public']) ? 'The results are public' : 'The results are private'
        this.shareResults_dialog_text = (this.deployment['public']) ? 'PUBLIC' : 'PRIVATE'
        this.shareResults_dialog_icon = (this.deployment['public']) ? 'fas fa-unlock' : 'fas fa-lock'

        // Add Deployment to the information table
        this.information_items = []
        this.information_items.push(this.deployment)

        // +---------------------+
        // | PARSE PROGRESS DATA |
        // +---------------------+
        if (data['progress']) {
          this.deployment['progress'] = JSON.parse(data['progress'])

          // Parse Last Updated
          this.last_updated = this.deployment['progress']['updated']

          // Calculate real-time overall
          if (data['overall'] == null && this.deployment['ended'] == null) {
            var diff = moment.utc().diff(moment(this.deployment['started']))
            this.deployment['overall'] = moment.utc(diff).format("HH:mm:ss")   
          }

          // Parse Validation
          this.parseValidation()

          // Parse Validation
          this.parseExecution()

          // Parse Logs
          this.parseLogs()

          // Parse Tasks
          this.parseTasks()

          // Parse Queries
          this.parseQueries()
        }
      },
      parseValidation() {
        if (!('validation' in this.deployment['progress'])) return
        // Init variables
        this.validation_headers = []
        this.validation_data = [{}]
        var i = 0

        // Fill variables
        for (let [key, value] of Object.entries(this.deployment['progress']['validation']).sort()) {
          this.validation_headers.push({ text: key, align: 'left', value: 'r' + i.toString(), sortable: false})
          var status = 'VALIDATING' 
          if ('success' in value) {
            status = (value['success'] ? 'SUCCEEDED' : 'FAILED')
            if (!this.validation_error && !value['success']) this.validation_error = true
          }
          this.validation_data[0]['r' + i.toString()] = status
          i += 1
        }
      },
      parseExecution() {
        // Init variables
        var execution_headers = []
        var execution_overall = [{}]
        var execution_progress = []
        var overall_progress = {}
        var i = 0

        // Init Execution Headers (if hasn't started yet)
        if (!('execution' in this.deployment['progress'])) {
          if (this.deployment['method'] != 'validate' && this.validation_data.length > 0) {
            var succeeded = true
            for (let i = 0; i < Object.values(this.validation_data[0]).length; ++i ) { 
              succeeded &= (Object.values(this.validation_data[0])[i] == 'SUCCEEDED')
            }
            if (succeeded) {
              this.execution_headers = JSON.parse(JSON.stringify(this.validation_headers))
              for (let i = 0; i < this.execution_headers.length; ++i) {
                execution_overall[0][[i]] = "Initiating..."
              }
            }
            this.execution_overall = JSON.parse(JSON.stringify(execution_overall))
          }
          return
        }

        // Init Execution Progress (if has started)
        for (let[key] of Object.entries(this.deployment['progress']['execution']).sort()) {
          overall_progress[[i]] = {"d": 0, "t": 0}
          execution_headers.push({ text: key, align: 'left', value: i, sortable: false})
          var j = 0
          for (let [key2, value2] of Object.entries(this.deployment['progress']['execution'][key])) {
            overall_progress[[i]]['d'] += value2['d']
            overall_progress[[i]]['t'] += value2['t']
            var progress = value2['p'] + '% (' + value2['d'] + '/' + value2['t'] + ' DBs)'

            if (j >= execution_progress.length) execution_progress.push({[[i]]: {"server": key2, "progress": progress}})
            else execution_progress[j][i] = {"server": key2, "progress": progress}
            j = j+1
          }
          
          // Add overall
          if (Object.entries(this.deployment['progress']['execution'][key]).length === 0) {
            if ('logs' in this.deployment['progress']) execution_overall[0][[i]] = "100% (0/0 DBs)"
            else execution_overall[0][[i]] = "Initiating..."
          }
          else {
            var execution_total = (overall_progress[[i]]['d'] / overall_progress[[i]]['t'] * 100).toFixed(2)
            if (execution_total == 100) execution_total = 100
            execution_overall[0][[i]] = execution_total + '% (' + overall_progress[[i]]['d'] + '/' + overall_progress[[i]]['t'] + ' DBs)'
          }
          i = i+1
        }
        // Sort Servers
        // execution_progress.sort((a, b) => (a[0].server > b[0].server) ? 1 : -1)

        // Assign variables
        this.execution_headers = JSON.parse(JSON.stringify(execution_headers))
        this.execution_overall = JSON.parse(JSON.stringify(execution_overall))
        this.execution_progress = JSON.parse(JSON.stringify(execution_progress))
      },
      parseLogs() {
        if (!('logs' in this.deployment['progress'])) return
        this.logs_data = this.deployment['progress']['logs']
      },
      parseTasks() {
        if (!('tasks' in this.deployment['progress'])) return
        this.tasks_data = this.deployment['progress']['tasks']
      },
      parseQueries() {
        if (!('queries' in this.deployment['progress'])) return
        // Init variables
        this.queries_data = []

        // Fill variables
        this.queries_data.push({
          total: this.deployment['progress']['queries']['total'],
          succeeded: this.deployment['progress']['queries']['succeeded']['t'] + ' (' + this.deployment['progress']['queries']['succeeded']['p'] + '%)',
          failed: this.deployment['progress']['queries']['failed']['t'] + ' (' + this.deployment['progress']['queries']['failed']['p'] + '%)',
          rollback: this.deployment['progress']['queries']['rollback']['t'] + ' (' + this.deployment['progress']['queries']['rollback']['p'] + '%)'
        })
      },
      showResults() {
        // Show Results View
        this.show_results = true
      },
      getExecutions() {
        // Get Deployment Executions
        axios.get('/deployments/executions', { params: { id: this.$route.params.id } })
          .then((response) => {
            this.executions['items'] = response.data.data
            this.executions['headers'] = [
              { text: 'Environment', value: 'environment' },
              { text: 'Mode', value: 'mode' },
              { text: 'Method', value: 'method' },
              { text: 'Status', value: 'status' },
              { text: 'Created', value: 'created' },
              { text: 'Started', value: 'started' },
              { text: 'Ended', value: 'ended' },
              { text: 'Overall', value: 'overall' },
              { text: 'Actions', value: 'actions' }
            ]
          })
          .catch((error) => {
            if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
      },
      // ------------------
      // NAVIGATION METHODS
      // ------------------
      parameters() {
        this.information_dialog_mode = 'parameters'
        this.information_dialog_execution_mode = this.deployment['mode']
        this.cmOptions.readOnly = true
        this.information_dialog_data = JSON.parse(JSON.stringify(this.deployment))
        this.schedule_enabled = this.deployment['scheduled'] !== null
        this.information_dialog = true
      },
      edit() {
        this.information_dialog_mode = (this.deployment['status'] == 'CREATED' || this.deployment['status'] == 'SCHEDULED') ? 'edit' : 're-deploy'
        this.information_dialog_execution_mode = this.deployment['mode']
        this.information_dialog_query_selected = []
        this.cmOptions.readOnly = false
        this.information_dialog_data = JSON.parse(JSON.stringify(this.deployment))
        this.schedule_enabled = this.deployment['scheduled'] !== null
        this.information_dialog = true
      },
      select() {
        this.select_dialog = true
      },
      start() {
        this.action_dialog_mode = 'start'
        this.action_dialog_title = 'START EXECUTION'
        this.action_dialog_text = 'Are you sure you want to start the current execution?'
        this.action_dialog = true
      },
      stop() {
        this.action_dialog_mode = 'stop'
        this.action_dialog_title = 'STOP EXECUTION'
        this.action_dialog_text = ''
        this.stop_execution_mode = (this.deployment['stopped'] == 'graceful') ? 'forceful' : 'graceful' 
        this.action_dialog = true
      },
      actionSubmit() {
        if (this.action_dialog_mode == 'start') this.actionSubmitStart()
        else if (this.action_dialog_mode == 'stop') this.actionSubmitStop()
      },
      actionSubmitStart() {
        // Start Current Execution
        this.notification('Starting the execution. Please wait...', 'primary')
        this.start_execution = true
        this.action_dialog = false
        
        // Build parameters
        const payload = {
          id: this.$route.params.id,
          url: window.location.protocol + '//' + window.location.host
        }
        axios.post('/deployments/start', payload)
        .then((response) => {
          if (response.data.message != '') this.notification(response.data.message, '#00b16a')
          this.getDeployment()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
      },
      actionSubmitStop() {
        if (!(['QUEUED','IN PROGRESS','STOPPING'].includes(this.deployment['status']))) this.notification('The execution has already finished.', 'warning')
        else {
          this.notification('Stopping the execution. Please wait...', 'primary')
          this.stop_execution = true

          // Build parameters
          const payload = {
            id: this.$route.params.id,
            mode: this.stop_execution_mode
          }
          axios.post('/deployments/stop', payload)
          .catch((error) => {
            if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
        }
        this.action_dialog = false
      },
      // ------------------------
      // SCHEDULE
      // ------------------------
      schedule_close() {
        this.scheduleDialog = false
        this.schedule_enabled = this.schedule_datetime != ''
        this.schedule_mode = 'date'
      },
      schedule_now() {
        const date = moment()
        if (this.schedule_mode == 'date') this.schedule_date = date.format("YYYY-MM-DD")
        else if (this.schedule_mode == 'time') this.schedule_time = date.format("HH:mm")
      },
      schedule_change() {
        if (this.schedule_enabled) {
          if (this.schedule_datetime == '') {
            const date = moment()
            this.schedule_date = date.format("YYYY-MM-DD")
            this.schedule_time = date.format("HH:mm")
          }
          this.scheduleDialog = true
        }
        else this.scheduleDialog = false
      },
      schedule_submit() {
        if (this.schedule_mode == 'date') {
          this.schedule_mode = 'time'
        }
        else if (this.schedule_mode == 'time') {
          this.schedule_datetime = this.schedule_date + ' ' + this.schedule_time
          this.schedule_mode = 'date'
          this.scheduleDialog = false
        }
      },
      // ------------------------
      // SELECT EXECUTION DIALOG
      // ------------------------
      selectExecution(id) {
        this.select_dialog = false
        if (this.deployment['id'] != id) {
          this.$router.push({ name:'deployment', params: { id: id }})
          this.show_results = false
          this.clear()
          this.init()
          this.getExecutions()
        }
      },
      // -------------------------------------
      // EDIT
      // -------------------------------------
      basicClick() {
        if (this.information_dialog_mode != 'parameters') this.information_dialog_execution_mode = 'BASIC'
      },
      proClick() {
        if (this.information_dialog_mode != 'parameters') this.information_dialog_execution_mode = 'PRO'
      },
      editSubmit() {
        if (!this.$refs.form.validate()) {
          this.notification('Please fill the required fields', '#EF5354')
          return
        }
        // Hide Results View
        this.show_results = false
        // Build parameters
        var payload = {
          id: this.$route.params.id,
          mode: this.information_dialog_execution_mode,
          environment: this.information_dialog_data.environment.id,
          method: this.information_dialog_data.method.toUpperCase(),
          scheduled: this.schedule_enabled ? moment(this.schedule_datetime).utc().format("YYYY-MM-DD HH:mm") + ':00' : null,
          start_execution: this.information_dialog_data.start_execution === undefined ? false : this.information_dialog_data.start_execution,
          url: window.location.protocol + '//' + window.location.host
        }
        // Build different modes
        if (this.information_dialog_execution_mode == 'BASIC') {
          payload['databases'] = this.information_dialog_data.databases
          payload['queries'] = JSON.stringify(this.information_dialog_data.queries)
        }
        else if (this.information_dialog_execution_mode == 'PRO') {
          payload['code'] = this.information_dialog_data.code
        }

        // Add deployment to the DB
        this.loading = true
        axios.put('/deployments', payload)
        .then((response) => {
          const data = response.data.data
          this.notification(response.data.message, '#00b16a')
          // Refresh user coins
          if ('coins' in data) this.$store.dispatch('app/coins', data['coins'])
          // Clear current deployment
          this.clear()
          // Get new deployment
          if (this.information_dialog_mode == 're-deploy' || payload['start_execution']) {
            this.$router.push({ name: 'deployment', params: { id: data['id'] }})
          }
          else this.getDeployment()
          // Get executions list
          this.getExecutions()
          // Hide the Information dialog
          this.information_dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
      },
      // -------------------------------------
      // QUERY
      // -------------------------------------
      newQuery() {
        this.query_dialog_mode = 'new'
        this.query_dialog_code = ''
        this.query_dialog_title = 'NEW QUERIES'
        this.query_dialog = true
      },
      editQuery () {
        this.query_dialog_mode = 'edit'
        this.query_dialog_code = this.information_dialog_query_selected[0]['query']
        this.query_dialog_title = 'EDIT QUERY'
        this.query_dialog = true
      },
      deleteQuery() {
        this.query_dialog_mode = 'delete'
        this.query_dialog_title = 'DELETE QUERY'
        this.query_dialog = true
      },
      cloneQuery() {
        let item = {id: this.information_dialog_data.queries.reduce((acc, val) => val.id > acc ? val.id : acc, 0)+1, query: this.information_dialog_query_selected[0].query}
        this.information_dialog_data.queries.push(item)
        this.information_dialog_query_selected = []
      },
      moveTopQuery() {
        let currentPos = this.information_dialog_data.queries.findIndex(x => x.id == this.information_dialog_query_selected[0].id)
        this.arraymove(this.information_dialog_data.queries, currentPos, 0)
      },
      moveUpQuery() {
        let currentPos = this.information_dialog_data.queries.findIndex(x => x.id == this.information_dialog_query_selected[0].id)
        if (currentPos > 0) this.arraymove(this.information_dialog_data.queries, currentPos, currentPos-1)
      },
      moveDownQuery() {
        let currentPos = this.information_dialog_data.queries.findIndex(x => x.id == this.information_dialog_query_selected[0].id)
        if (currentPos < this.information_dialog_data.queries.length-1) this.arraymove(this.information_dialog_data.queries, currentPos, currentPos+1)
      },
      moveBottomQuery() {
        let currentPos = this.information_dialog_data.queries.findIndex(x => x.id == this.information_dialog_query_selected[0].id)
        this.arraymove(this.information_dialog_data.queries, currentPos, this.information_dialog_data.queries.length-1)
      },
      arraymove(arr, fromIndex, toIndex) {
        let element = arr[fromIndex]
        arr.splice(fromIndex, 1)
        arr.splice(toIndex, 0, element)
      },
      queryActionConfirm() {
        if (this.query_dialog_mode == 'new') this.newQueryConfirm()
        else if (this.query_dialog_mode == 'edit') this.editQueryConfirm()
        else if (this.query_dialog_mode == 'delete') this.deleteQueryConfirm()
      },
      newQueryConfirm() {
        // Check if all fields are filled
        if (this.query_dialog_code.trim().length == 0) {
          this.notification('Please enter a query', '#EF5354')
          return
        }

        // Parse Queries
        var queries = this.parseQueriesFormat()

        // Add queries into the data table
        for (var q = 0; q < queries.length; ++q) {
          if (queries[q]['query'] != ';') this.information_dialog_data.queries.push(queries[q])
        }

        // Post-tasks
        this.information_dialog_query_selected = []
        this.query_dialog = false
        this.notification('Queries added successfully', '#00b16a')
      },
      editQueryConfirm() {
        // Parse Queries
        if (this.parseQueriesFormat().length > 1) {
          this.notification('Multiple queries detected', '#EF5354')
          return
        }

        // Get Item Position
        for (var i = 0; i < this.information_dialog_data.queries.length; ++i) {
          if (this.information_dialog_data.queries[i]['id'] == this.information_dialog_query_selected[0]['id']) break
        }

        // Edit item in the data table
        this.information_dialog_data.queries.splice(i, 1, {"id": this.query_dialog_code[i]['id'], "query": this.query_dialog_code})
        this.information_dialog_query_selected = []
        this.query_dialog = false
        this.notification('Query edited successfully', '#00b16a')
      },
      deleteQueryConfirm() {
        while(this.information_dialog_query_selected.length > 0) {
          var s = this.information_dialog_query_selected.pop()
          for (var i = 0; i < this.information_dialog_data.queries.length; ++i) {
            if (this.information_dialog_data.queries[i]['id'] == s['id']) {
              // Delete Item
              this.information_dialog_data.queries.splice(i, 1)
              break
            }
          }
        }
        this.notification('Selected queries removed successfully', '#00b16a')
        this.query_dialog = false
      },
      parseQueriesFormat() {
        // Build multi-queries
        var id = (this.information_dialog_data.queries.length == 0) ? 1: this.information_dialog_data.queries.reduce((acc, val) => val.id > acc ? val.id : acc, 0)+1
        var queries = []
        var start = 0;
        var chars = []
        for (var i = 0; i < this.query_dialog_code.length; ++i) {
          if (this.query_dialog_code[i] == ';' && chars.length == 0) {
            queries.push({"id": id, "query": this.query_dialog_code.substring(start, i+1).trim()})
            id += 1
            start = i+1
          }
          else if (this.query_dialog_code[i] == "\"") {
            if (chars[chars.length-1] == '"') chars.pop()
            else chars.push("\"")
          }
          else if (this.query_dialog_code[i] == "'") {
            if (chars[chars.length-1] == "'") chars.pop()
            else chars.push("'")
          }
        }
        if (start < i) queries.push({"id": id, "query": this.query_dialog_code.substring(start, i).trim()})
        // Return parsed queries
        return queries
      },
      // -------------------------------------
      // SHARE RESULTS
      // -------------------------------------
      resultsClipboard() {
        navigator.clipboard.writeText(this.url + `/viewer/` + this.deployment['uri'])
        this.notification('Link copied to clipboard', 'primary')
      },
      resultsShare() {
        // Build parameters
        const payload = {
          id: this.$route.params.id,
          public: !this.deployment['public']
        }
        axios.post('/deployments/public', payload)
        .then(() => {
          // Update new public value
          this.deployment['public'] = !this.deployment['public']
          this.shareResults_dialog_title = (this.deployment['public']) ? 'The results are public' : 'The results are private'
          this.shareResults_dialog_text = (this.deployment['public']) ? 'PUBLIC' : 'PRIVATE'
          this.shareResults_dialog_icon = (this.deployment['public']) ? 'fas fa-unlock' : 'fas fa-lock'

          if (this.deployment['public']) this.notification('Results changed to public', 'info')
          else this.notification('Results changed to private', 'info')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
      },
      // -------------------------------------
      // AUXILIARY METHODS
      // -------------------------------------
      selectRow(id) {
        if (id == this.deployment['id']) return '#616161'
        else return '#424242'
      },
      getMethodColor (method) {
        if (method == 'DEPLOY') return '#EF5354'
        else if (method == 'TEST') return '#ff9800'
        else if (method == 'VALIDATE') return '#4caf50'
      },
      getModeColor (mode) {
        if (mode == 'BASIC') return 'rgb(250, 130, 49)'
        else if (mode == 'PRO') return 'rgb(235, 95, 93)'
      },
      regionColor (index, region) {
        if (region.startsWith('100%')) return 'background-color: rgb(0, 177, 106);'
        else return 'background-color: rgb(250, 130, 49);'
      },
      regionIcon (progress) {
        if (progress.startsWith('100%')) return 'fas fa-check'
        else return 'fas fa-spinner'  
      },
      serverColor (progress) {
        if (progress.startsWith('100%')) return 'color: #00b16a;'
        else return 'color: rgb(250, 130, 49);'
      },
      dateFormat(date) {
        if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
        return date
      },
      notification(message, color) {
        this.snackbarText = message
        this.snackbarColor = color 
        this.snackbar = true
      },
      checkNotifications() {
        if (this.$route.params.msg) this.notification(this.$route.params.msg, this.$route.params.color)
      },
      index (data) {
        return data.map((item, index) => ({
          i: index,
          ...item
        }))
      }
    },
    watch: {
      query_dialog (val) {
        if (!val) return
        this.cmOptions2.readOnly = true
        this.$nextTick(() => {
          if (this.$refs.codemirror === undefined) return
          const codemirror = this.$refs.codemirror.codemirror
          setTimeout(() => { codemirror.refresh(); codemirror.focus(); this.cmOptions2.readOnly = false }, 200)
        })
      },
      '$route' () {
        this.init()
      },
      information_dialog(val) {
        if (!val) this.information_dialog_data.code = ''
      },
      information_dialog_execution_mode (val) {
        if (val == 'PRO') {
          this.$nextTick(() => {
            if (this.$refs.myCm === undefined) return
            const codemirror = this.$refs.myCm.codemirror
            if (this.information_dialog_data.code.length == 0) {
              this.information_dialog_data.code = this.code
              codemirror.setValue(this.information_dialog_data.code)
            }
            this.information_dialog_data.code = this.information_dialog_data.code.length == 0 ? this.code : this.information_dialog_data.code
            codemirror.refresh()
          })
        }
      },
    }
  }
</script>