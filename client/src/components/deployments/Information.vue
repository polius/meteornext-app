<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">INFORMATION</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>

        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn v-if="'status' in deployment" text title="Show Parameters" @click="parameters()"><v-icon small style="padding-right:10px">fas fa-cog</v-icon>PARAMETERS</v-btn>
          <v-btn v-if="'status' in deployment" text title="Select Execution" @click="select()"><v-icon small style="padding-right:10px">fas fa-mouse-pointer</v-icon>SELECT</v-btn>
          <v-btn :disabled="deployment['status'] == 'STARTING' || deployment['status'] == 'IN PROGRESS' || deployment['status'] == 'STOPPING'" v-if="'status' in deployment" text :title="(deployment['status'] == 'CREATED') ? 'Edit execution' : 'Re-Deploy with other parameters'" @click="edit()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>{{(deployment['status'] == 'CREATED') ? 'EDIT' : 'RE-DEPLOY'}}</v-btn>
          <v-divider v-if="start_execution || deployment['status'] == 'STARTING' || deployment['status'] == 'CREATED' || deployment['status'] == 'IN PROGRESS' || deployment['status'] == 'STOPPING'" class="mx-3" inset vertical></v-divider>
          <v-btn :disabled="start_execution" v-if="deployment['status'] == 'CREATED'" text title="Start Execution" @click="start()"><v-icon small style="padding-right:10px">fas fa-play</v-icon>START</v-btn>
          <v-btn :disabled="stop_execution || deployment['status'] == 'STARTING' || deployment['status'] == 'STOPPING'" v-if="deployment['status'] == 'STARTING' || deployment['status'] == 'STOPPING' || deployment['status'] == 'IN PROGRESS'" text title="Stop Execution" @click="stop()"><v-icon small style="padding-right:10px">fas fa-ban</v-icon>STOP</v-btn>
        </v-toolbar-items>
        <v-divider v-if="'status' in deployment" class="mx-3" inset vertical></v-divider>
        
        <div v-if="(stop_execution && deployment['status'] != 'STOPPED') || deployment['status'] == 'STOPPING'" class="subtitle-1" style="margin-left:5px;">Stopping the execution...</div>
        <div v-else-if="(start_execution && deployment['status'] == 'IN PROGRESS') || deployment['status'] == 'IN PROGRESS'" class="subtitle-1" style="margin-left:5px;">Execution in progress...</div>
        <div v-else-if="start_execution || deployment['status'] == 'STARTING'" class="subtitle-1" style="margin-left:5px;">Starting the execution...</div>
        <v-progress-circular v-if="start_execution || (stop_execution && deployment['status'] != 'STOPPED') || deployment['status'] == 'STARTING' || deployment['status'] == 'STOPPING' ||  deployment['status'] == 'IN PROGRESS'" :size="22" indeterminate color="white" width="2" style="margin-left:20px; margin-right:10px;"></v-progress-circular>

        <v-chip v-if="deployment['status'] == 'SUCCESS'" label color="success" style="margin-left:5px; margin-right:15px;">SUCCESS</v-chip>
        <v-chip v-else-if="deployment['status'] == 'WARNING'" label color="warning" style="margin-left:5px; margin-right:15px;" title="Some queries failed">WARNING</v-chip>
        <v-chip v-else-if="deployment['status'] == 'FAILED'" label color="error" style="margin-left:5px; margin-right:15px;">FAILED</v-chip>
        <v-chip v-else-if="deployment['status'] == 'STOPPED'" label color="error" style="margin-left:5px; margin-right:15px;">STOPPED</v-chip>

        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn v-if="show_results" text title="Show Execution Progress" @click="show_results = false"><v-icon small style="padding-right:10px;">fas fa-spinner</v-icon>PROGRESS</v-btn>
          <v-btn v-if="show_results" text title="Share Results" @click="shareResults_dialog = true"><v-icon small style="padding-right:10px;">fas fa-link</v-icon>SHARE</v-btn>
          <v-btn v-else-if="deployment['status'] == 'SUCCESS' || deployment['status'] == 'WARNING' || (deployment['status'] == 'FAILED' && !validation_error) || (deployment['status'] == 'STOPPED' && deployment['uri'] != null)" text title="Show Execution Results" @click="showResults()"><v-icon small style="padding-right:10px;">fas fa-meteor</v-icon>RESULTS</v-btn>
        </v-toolbar-items>

        <v-spacer></v-spacer>
        <div v-if="last_updated != ''" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ last_updated }}</b> UTC</div>
        <v-btn icon @click="goBack()"><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn>
      </v-toolbar>

      <!-- RESULTS -->
      <v-card-text v-if="show_results" style="padding:0px; background-color:rgb(55, 53, 64);">
        <results :src="deployment['uri']" :height="`calc(100vh - 207px)`"></results>
      </v-card-text>

      <v-card-text v-else>
        <!-- INFORMATION -->
        <v-card>
          <v-data-table :headers="information_headers" :items="information_items" hide-default-footer class="elevation-1">
            <template v-slot:item.mode="props">
              <v-chip :color="getModeColor(props.item.mode)">{{ props.item.mode }}</v-chip>
            </template>
            <template v-slot:item.method="props">
              <span :style="'color: ' + getMethodColor(props.item.method.toUpperCase())" style="font-weight:500">{{ props.item.method.toUpperCase() }}</span>
            </template>
            <template v-slot:item.status="props">
              <v-icon v-if="props.item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
              <v-icon v-else-if="props.item.status == 'QUEUED'" title="Queued" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
              <v-icon v-else-if="props.item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
              <v-icon v-else-if="props.item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
              <v-icon v-else-if="props.item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
              <v-icon v-else-if="props.item.status == 'WARNING'" title="Some queries failed" small style="color: #ff9800; margin-left:9px;">fas fa-check</v-icon>
              <v-icon v-else-if="props.item.status == 'FAILED'" title="Failed" small style="color: #f44336; margin-left:11px;">fas fa-times</v-icon>
              <v-icon v-else-if="props.item.status == 'STOPPING'" title="Stopping" small style="color: #ff9800; margin-left:8px;">fas fa-ban</v-icon>
              <v-icon v-else-if="props.item.status == 'STOPPED'" title="Stopped" small style="color: #f44336; margin-left:8px;">fas fa-ban</v-icon>
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
        <div v-if="validation_data.length > 0" class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">VALIDATION</div>
        <!-- validation -->
        <v-card v-if="validation_data.length > 0" style="margin-top:15px;">
          <v-data-table :headers="validation_headers" :items="validation_data" hide-default-footer>
            <template v-slot:item="props">
              <tr>
                <td v-for="item in Object.keys(validation_data[0])" :key="item">
                  <span v-if="validation_data[0][item] == 'VALIDATING'" class="warning--text"><v-icon small color="warning" style="margin-right:10px;">fas fa-spinner</v-icon><b>{{ validation_data[0][item] }}</b></span>
                  <span v-else-if="validation_data[0][item] == 'SUCCEEDED'" class="success--text"><v-icon small color="success" style="margin-right:10px;">fas fa-check</v-icon><b>{{ validation_data[0][item] }}</b></span>
                  <span v-else-if="validation_data[0][item] == 'FAILED'" class="error--text"><v-icon small color="error" style="margin-right:10px;">fas fa-times</v-icon><b>{{ validation_data[0][item] }}</b></span>
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
        <div v-if="execution_data.length > 0" class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">EXECUTION</div>
        <v-card v-if="execution_data.length > 0" style="margin-top:15px;">
          <v-data-table :headers="execution_headers" :items="this.index(execution_data)" hide-default-footer>
            <template v-slot:item="props">
              <tr>
                <td v-for="item in Object.keys(execution_headers)" :key="item" :style="regionColor(props.item.i, execution_data[props.item.i][item])">
                  <span v-if="props.item.i == 0"><v-icon small style="margin-right:10px;">{{ regionIcon(execution_data[props.item.i][item]) }}</v-icon><b>{{ execution_data[props.item.i][item] }}</b></span>
                  <span v-else-if="item in execution_data[props.item.i]" :class="serverColor(execution_data[props.item.i][item]['progress'])"><b>{{ execution_data[props.item.i][item]['server'] }}</b> {{ execution_data[props.item.i][item]['progress'] }}</span>
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
                  <v-flex xs12 style="padding-left:5px; padding-right:5px; padding-bottom:10px;">
                    <v-textarea :value="deployment['progress']['error']" color="#c6c6c6" auto-grow solo flat readonly hide-details></v-textarea>
                  </v-flex>
                </v-layout>
              </v-container>
            </v-card-text>
          </v-card>
        </div>

        <!-- After Execution Headers -->
        <v-layout row wrap style="margin:0px;">
          <v-flex xs8>
            <div v-if="logs_data.length > 0 || tasks_data.length > 0" class="title font-weight-regular" style="padding-top:20px; padding-left:1px;">POST EXECUTION</div>
          </v-flex>
          <v-flex xs4>
            <div v-if="queries_data.length > 0" class="title font-weight-regular" style="padding-top:20px; padding-left:7px;">QUERIES</div>
          </v-flex>
        </v-layout>

        <!-- POST EXECUTION -->
        <v-layout row wrap style="margin-top:15px; margin-left:0px; margin-right:0px;">
          <!-- logs -->
          <v-flex v-if="logs_data.length > 0" xs4 style="padding-right:5px;">
            <v-card>
              <v-data-table :headers="logs_headers" :items="logs_data" hide-default-footer>
              </v-data-table>
            </v-card>
          </v-flex>
          <!-- remaining-tasks -->
          <v-flex v-if="tasks_data.length > 0" xs4 style="padding-left:5px; padding-right:5px;">
            <v-card>
              <v-data-table :headers="tasks_headers" :items="tasks_data" hide-default-footer>
              </v-data-table>
            </v-card>
          </v-flex>
          <!-- queries -->
          <v-flex v-if="queries_data.length > 0" xs4 style="padding-left:5px;">
            <v-card>
              <v-data-table :headers="queries_headers" :items="queries_data" hide-default-footer>
              </v-data-table>
            </v-card>
          </v-flex>
        </v-layout>
      </v-card-text>
    </v-card>

    <v-dialog v-model="information_dialog" persistent no-click-animation max-width="70%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ information_dialog_mode.toUpperCase() }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="information_dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div class="title font-weight-regular" style="margin-top:10px; margin-bottom: 25px;">{{ this.deploymentMode }}</div>
                <v-text-field readonly v-model="information_dialog_data.name" label="Name" style="padding-top:0px;"></v-text-field>
                <v-select v-if="deploymentMode != 'PRO'" :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.environment" :items="[information_dialog_data.environment]" label="Environment" style="padding-top:0px;"></v-select>

                <v-select v-if="deploymentMode == 'INBENTA'" :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.products" :items="information_dialog_data.products_list" label="Products" multiple style="padding-top:0px;"></v-select>
                <v-select v-if="deploymentMode == 'INBENTA'" :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schema" :items="information_dialog_data.schema_list" label="Schema" style="padding-top:0px;"></v-select>

                <v-text-field v-if="deploymentMode != 'PRO'" :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.databases" label="Databases" hint="Separated by commas. Wildcards allowed: % _" style="padding-top:0px;"></v-text-field>
                <v-card v-if="deploymentMode != 'PRO'" style="margin-bottom:20px;">
                  <v-toolbar flat dense color="#2e3131" style="margin-top:5px;">
                    <v-toolbar-title class="white--text">Queries</v-toolbar-title>
                    <v-divider v-if="information_dialog_mode != 'parameters'" class="mx-3" inset vertical></v-divider>
                    <v-toolbar-items v-if="information_dialog_mode != 'parameters'" class="hidden-sm-and-down" style="padding-left:0px;">
                      <v-btn text @click='newQuery()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                      <v-btn v-if="information_dialog_query_selected.length == 1" text @click="editQuery()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                      <v-btn v-if="information_dialog_query_selected.length > 0" text @click='deleteQuery()'><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                    </v-toolbar-items>
                  </v-toolbar>
                  <v-divider></v-divider>
                  <v-data-table v-model="information_dialog_query_selected" :headers="information_dialog_data.query_headers" :items="information_dialog_data.queries" item-key="query" :show-select="information_dialog_mode != 'parameters'" :hide-default-header="information_dialog_mode == 'parameters'" hide-default-footer class="elevation-1">
                  </v-data-table>
                </v-card>

                <div v-if="deploymentMode == 'PRO'" class="subtitle-1 font-weight-regular" style="margin-top:-5px; margin-bottom:10px;" title="Press ESC when cursor is in the editor to toggle full screen editing">CODE</div>
                <codemirror v-if="deploymentMode == 'PRO'" v-model="information_dialog_data.code" :options="cmOptions" style="margin-bottom:15px;"></codemirror>

                <div class="subtitle-1 font-weight-regular">METHOD</div>
                <v-radio-group :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.method" hide-details style="margin-top:10px;">
                  <v-radio value="validate" color="success">
                    <template v-slot:label>
                      <div class="success--text">VALIDATE</div>
                    </template>
                  </v-radio>
                  <v-radio value="test" color="orange">
                    <template v-slot:label>
                      <div class="orange--text">TEST</div>
                    </template>
                  </v-radio>
                  <v-radio value="deploy" color="red">
                    <template v-slot:label>
                      <div class="red--text">DEPLOY</div>
                    </template>
                  </v-radio>
                </v-radio-group>

                <v-checkbox v-if="information_dialog_mode != 'parameters' && deployment['status'] != 'CREATED'" :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.start_execution" label="Start execution" color="primary" hide-details></v-checkbox>
                <v-divider v-if="information_dialog_mode != 'parameters'" style="margin-top:15px;"></v-divider>

                <div v-if="information_dialog_mode != 'parameters'" style="margin-top:20px;">
                  <v-btn color="success" @click="editSubmit()">CONFIRM</v-btn>
                  <v-btn color="error" @click="information_dialog = false" style="margin-left:10px;">CANCEL</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="query_dialog" persistent max-width="600px">
      <v-toolbar color="primary">
        <v-toolbar-title class="white--text">{{ query_dialog_title }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="query_dialog_mode!='delete'">
                <v-form ref="query_form">
                  <v-textarea ref="field" rows="1" filled auto-grow v-model="query_dialog_item" label="Query" :rules="[v => !!v || '']" required></v-textarea>
                </v-form>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="query_dialog_mode=='delete'">
                <div class="subtitle-1">Are you sure you want to delete the selected queries?</div>
              </v-flex>
              <v-btn color="success" @click="queryActionConfirm()">Confirm</v-btn>
              <v-btn color="error" @click="query_dialog=false" style="margin-left:10px">Cancel</v-btn>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="select_dialog" max-width="80%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">SELECT EXECUTION</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="select_dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 15px 20px 20px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-card>
                  <v-toolbar flat dense color="#2e3131">
                    <v-toolbar-title class="white--text">Executions</v-toolbar-title>
                  </v-toolbar>
                  <v-divider></v-divider>
                  <v-data-table :headers="executions.headers" :items="executions.items" item-key="id" class="elevation-1">
                    <template v-slot:item="props">
                      <tr :style="`background-color:` + selectRow(props.item.id)">
                        <td>{{ props.item.environment }}</td>
                        <td><span :style="'color: ' + getMethodColor(props.item.method.toUpperCase())" style="font-weight:500">{{ props.item.method.toUpperCase() }}</span></td>
                        <td>{{ props.item.created }}</td>
                        <td>
                          <v-icon v-if="props.item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
                          <v-icon v-else-if="props.item.status == 'QUEUED'" title="Queued" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
                          <v-icon v-else-if="props.item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
                          <v-icon v-else-if="props.item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
                          <v-icon v-else-if="props.item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
                          <v-icon v-else-if="props.item.status == 'WARNING'" title="Some queries failed" small style="color: #ff9800; margin-left:9px;">fas fa-check</v-icon>
                          <v-icon v-else-if="props.item.status == 'FAILED'" title="Failed" small style="color: #f44336; margin-left:11px;">fas fa-times</v-icon>
                          <v-icon v-else-if="props.item.status == 'STOPPING'" title="Stopping" small style="color: #ff9800; margin-left:8px;">fas fa-ban</v-icon>
                          <v-icon v-else-if="props.item.status == 'STOPPED'" title="Stopped" small style="color: #f44336; margin-left:8px;">fas fa-ban</v-icon>
                        </td>
                        <td>{{ props.item.started }}</td>
                        <td>{{ props.item.ended }}</td>
                        <td>{{ props.item.overall }}</td>
                        <td><v-btn icon small @click="selectExecution(props.item.id)"><v-icon small title="Select execution">fas fa-arrow-right</v-icon></v-btn></td>
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
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ action_dialog_title }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text style="padding: 10px 20px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div class="subtitle-1" style="margin-bottom:10px">{{ action_dialog_text }}</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn color="success" @click="actionSubmit()">Confirm</v-btn>
                  <v-btn color="error" @click="action_dialog=false" style="margin-left:10px;">Cancel</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="shareResults_dialog" max-width="896px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">SHARE RESULTS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-toolbar-items class="hidden-sm-and-down">
            <v-btn text :title="shareResults_dialog_title" @click="resultsShare()"><v-icon small style="padding-right:10px">{{ shareResults_dialog_icon }}</v-icon>{{ shareResults_dialog_text }}</v-btn>
            <v-btn text title="Copy link to clipboard" @click="resultsClipboard()"><v-icon small style="padding-right:10px">fas fa-clipboard</v-icon>CLIPBOARD</v-btn>
          </v-toolbar-items>
          <v-spacer></v-spacer>
          <v-btn icon @click="shareResults_dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 style="padding-bottom:10px">
                <v-btn ref="results_url" block text :href="`http://` + url + `/results/` + deployment['uri']" target="_blank" class="text-lowercase title font-weight-light" style="margin-top:25px;">{{ url + `/results/` + deployment['uri'] }}</v-btn>
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
</template>

<style>
.CodeMirror {
  min-height:450px;
  font-size: 14px;
}
.CodeMirror pre {
  padding: 0 14px;
}
</style>

<script>
  import axios from 'axios'

  // CODE-MIRROR
  import { codemirror } from 'vue-codemirror'
  import 'codemirror/lib/codemirror.css'

  // language
  import 'codemirror/mode/python/python.js'
  // theme css
  import 'codemirror/theme/monokai.css'

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
  import Results from './Results'

  export default  {
    data: () => ({
      // Deployment Data
      deployment: {},

      // Deployment Executions
      executions: {},

      // Last Updated
      last_updated: '',

      // Information
      information_headers: [
        { text: 'Name', value: 'name', sortable: false },
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
      execution_data: [],

      // Post Execution
      logs_headers: [{ text: 'LOGS', align:'left', value: 'status', sortable: false }],
      logs_data: [],
      tasks_headers: [{ text: 'REMAINING TASKS', align:'left', value: 'status', sortable: false }],
      tasks_data: [],
      queries_headers: [
        { text: 'TOTAL', align:'left', value: 'total', sortable: false },
        { text: 'SUCCEEDED', align:'left', value: 'succeeded', sortable: false },
        { text: 'FAILED', align:'left', value: 'failed', sortable: false }
      ],
      queries_data: [],
      
      // Dialogs
      // - Information -
      information_dialog: false,
      information_dialog_mode: '',
      information_dialog_data: {},
      information_dialog_query_selected: [],
      // - Query -
      query_dialog: false,
      query_dialog_mode: '',
      query_dialog_title: '',
      query_dialog_item: '',
      // - Select -
      select_dialog: false,
      // - Action -
      action_dialog: false,
      action_dialog_title: '',
      action_dialog_text: '',
      action_dialog_mode: '',

      // Share Results Dialog
      shareResults_dialog: false,
      shareResults_dialog_title: '',
      shareResults_dialog_text: '',
      shareResults_dialog_icon: '',

      // Executions Flag
      stop_execution: false,
      start_execution: false,
      show_results: false,

      // Init Code Parameters
      cmOptions: {
        readOnly: true,
        autoCloseBrackets: true,
        styleActiveLine: true,
        lineNumbers: true,
        tabSize: 4,
        line: true,
        foldGutter: true,
        matchBrackets: true,
        showCursorWhenSelecting: true,
        mode: 'python',
        theme: 'monokai',
        keyMap: 'sublime',
        extraKeys: {
          "Tab": function(cm) { 
            cm.replaceSelection("    " , "end"); 
          },
          "Esc": function(cm) {
            cm.setOption("fullScreen", !cm.getOption("fullScreen"))
          }
        }
      },

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: '',

      url: window.location.host
    }),
    props: ['executionID', 'deploymentMode'],
    components: { 
      codemirror,
      results: Results
    },
    created() {
      if (typeof this.executionID === "undefined") this.$router.go(-1)
      else {
        // Init parameters and get deployment
        this.deployment['execution_id'] = this.executionID
        this.deployment['mode'] = this.deploymentMode
        this.getDeployment()
      }
    },
    methods: {
      // -------------
      // BASE METHODS
      // -------------
      goBack() {
        this.$router.go(-1)
      },
      getDeployment() {
        // Get Deployment Data
        const path = '/deployments/' + this.deployment['mode'].toLowerCase()
        axios.get(path, { params: { execution_id: this.deployment['execution_id'] } })
          .then((response) => {
            const data = response.data.data[0]
            this.parseRequest(data)
            if (this.$router.currentRoute.name == 'deployments.information') {
              if (data['status'] == 'STARTING' || data['status'] == 'STOPPING' || data['status'] == 'IN PROGRESS') setTimeout(this.getDeployment, 2000)
              else this.start_execution = false
            }
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message, 'error')
          })
      },
      clear() {
        this.validation_data = []
        this.execution_data = []
        this.logs_data = []
        this.tasks_data = []
        this.queries_data = []
        delete this.deployment.progress.error
        
        this.validation_error = false
        this.start_execution = false
        this.stop_execution = false
      },
      parseRequest(data) {
        // Parse Deployment Data
        this.deployment['id'] = data['id']
        this.deployment['deployment_id'] = data['deployment_id']
        this.deployment['mode'] = data['mode']
        this.deployment['name'] = data['name']
        this.deployment['environment'] = data['environment']
        if (this.deployment['mode'] == 'BASIC' || this.deployment['mode'] == 'INBENTA') {
          this.deployment['databases'] = data['databases']
          this.deployment['queries'] = []
          var queries = JSON.parse(data['queries'])
          for (var i in queries) this.deployment['queries'].push(queries[i])
          this.deployment['query_headers'] = [{text: 'Query', value: 'query'}]
        }
        else if (this.deployment['mode'] == 'PRO') {
          this.deployment['code'] = data['code']
        }
        if (this.deployment['mode'] == 'INBENTA') {
          this.deployment['products_schema'] = data['products_list']
          this.deployment['products_list'] = Object.keys(data['products_list'])
          this.deployment['products'] = []
          for (const i of data['products'].split(',')) {
            for (const [key, value] of Object.entries(data['products_list'])) {
              if (i == value) this.deployment['products'].push(key)
            }
          }
          this.deployment['schema_list'] = data['schema_list']
          this.deployment['schema'] = data['schema']
        }
        this.deployment['method'] = data['method'].toLowerCase()
        this.deployment['status'] = data['status']
        this.deployment['created'] = data['created']
        this.deployment['started'] = data['started']
        this.deployment['ended'] = data['ended']
        this.deployment['overall'] = data['overall']
        this.deployment['error'] = data['error']
        this.deployment['uri'] = data['uri']
        this.deployment['url'] = data['url']
        this.deployment['engine'] = data['engine']
        this.deployment['public'] = data['public']

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
        // Get Executions
        this.getExecutions()
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
        if (!('execution' in this.deployment['progress'])) return
        // Init variables
        this.execution_headers = []
        this.execution_data = [{}]
        var overall_progress = {}
        var i = 0

        // Fill variables
        for (let[key] of Object.entries(this.deployment['progress']['execution']).sort()) {
          overall_progress[[i]] = {"d": 0, "t": 0}
          this.execution_headers.push({ text: key, align: 'left', value: i, sortable: false})
          var j = 0
          for (let [key2, value2] of Object.entries(this.deployment['progress']['execution'][key])) {
            overall_progress[[i]]['d'] += value2['d']
            overall_progress[[i]]['t'] += value2['t']
            var progress = value2['p'] + '% (' + value2['d'] + '/' + value2['t'] + ' DBs)'

            if (j+1 >= this.execution_data.length) this.execution_data.push({[[i]]: {"server": key2, "progress": progress}})
            else this.execution_data[j+1][i] = {"server": key2, "progress": progress}
            j = j+1
          }
          
          // Add overall
          if (Object.entries(this.deployment['progress']['execution'][key]).length === 0) {
            if ('logs' in this.deployment['progress']) this.execution_data[0][[i]] = "100% (0/0 DBs)"
            else this.execution_data[0][[i]] = "Initiating..."
          }
          else this.execution_data[0][[i]] = overall_progress[[i]]['d'] / overall_progress[[i]]['t'] * 100 + '% (' + overall_progress[[i]]['d'] + '/' + overall_progress[[i]]['t'] + ' DBs)'
          i = i+1
        }
      },
      parseLogs() {
        if (!('logs' in this.deployment['progress'])) return
        // Init variables
        this.logs_data = []

        // Fill variables
        for (var i in this.deployment['progress']['logs']) {
          this.logs_data.push({status: this.deployment['progress']['logs'][i]})
        }
      },
      parseTasks() {
        if (!('tasks' in this.deployment['progress'])) return
        // Init variables
        this.tasks_data = []

        // Fill variables
        for (var i in this.deployment['progress']['tasks']) {
          this.tasks_data.push({status: this.deployment['progress']['tasks'][i]})
        }
      },
      parseQueries() {
        if (!('queries' in this.deployment['progress'])) return
        // Init variables
        this.queries_data = []

        // Fill variables
        this.queries_data.push({
          total: this.deployment['progress']['queries']['total'],
          succeeded: this.deployment['progress']['queries']['succeeded']['t'] + ' (' + this.deployment['progress']['queries']['succeeded']['p'] + '%)',
          failed: this.deployment['progress']['queries']['failed']['t'] + ' (' + this.deployment['progress']['queries']['failed']['p'] + '%)'
        })
      },
      showResults() {
        // Show Results View
        this.show_results = true
      },
      getExecutions() {
        // Get Deployment Executions
        const path = '/deployments/' + this.deployment['mode'].toLowerCase() + '/executions'
        axios.get(path, { params: { deployment_id: this.deployment['id'] } })
          .then((response) => {
            this.executions['items'] = response.data.data
            this.executions['headers'] = [
              { text: 'Environment', value: 'environment' },
              { text: 'Method', value: 'method' },
              { text: 'Created', value: 'created' },
              { text: 'Status', value: 'status' },
              { text: 'Started', value: 'started' },
              { text: 'Ended', value: 'ended' },
              { text: 'Overall', value: 'overall' },
              { text: 'Actions', value: 'actions' }
            ]
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message, 'error')
          })
      },
      // ------------------
      // NAVIGATION METHODS
      // ------------------
      parameters() {
        this.information_dialog_mode = 'parameters'
        this.cmOptions.readOnly = true
        this.information_dialog_data = JSON.parse(JSON.stringify(this.deployment))
        this.information_dialog = true
      },
      edit() {
        this.information_dialog_mode = (this.deployment['status'] == 'CREATED') ? 'edit' : 're-deploy'
        this.cmOptions.readOnly = false
        this.information_dialog_data = JSON.parse(JSON.stringify(this.deployment))
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
        this.action_dialog_text = 'Are you sure you want to stop the current execution?'
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
        const path = '/deployments/' + this.deployment['mode'].toLowerCase() +  '/start'
        const payload = {
          execution_id: this.deployment['execution_id']
        }
        axios.post(path, payload)
        .then((response) => {
          this.notification(response.data.message, 'success')
          this.getDeployment()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
      },
      actionSubmitStop() {
        if (this.deployment['status'] != 'IN PROGRESS') this.notification('The execution has already finished.', 'primary')
        else {
          this.notification('Stopping the execution. Please wait...', 'primary')
          this.stop_execution = true

          // Build parameters
          const path = '/deployments/' + this.deployment['mode'].toLowerCase() +  '/stop'
          const payload = {
            execution_id: this.deployment['execution_id']
          }
          axios.post(path, payload)
          .then(() => {
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message, 'error')
          })
        }
        this.action_dialog = false
      },
      // ------------------------
      // SELECT EXECUTION DIALOG
      // ------------------------
      selectExecution(execution_id) {
        this.clear()
        this.deployment['execution_id'] = execution_id
        this.getDeployment()
        this.select_dialog = false
      },
      // -------------------------------------
      // EDIT
      // -------------------------------------
      editSubmit() {
        // Hide Results View
        this.show_results = false
        // Build parameters
        const path = '/deployments/' + this.deployment['mode'].toLowerCase()
        var payload = {
          id: this.deployment.id,
          execution_id: this.deployment.execution_id,
          name: this.deployment.name,
          environment: this.information_dialog_data.environment,
          mode: this.deployment['mode'].toUpperCase(),
          method: this.information_dialog_data.method.toUpperCase(),
          start_execution: (this.information_dialog_data.start_execution === undefined) ? false : this.information_dialog_data.start_execution
        }
        // Build different modes
        if (this.deployment['mode'] == 'BASIC' || this.deployment['mode'] == 'INBENTA') {
          payload['databases'] = this.information_dialog_data.databases
          payload['queries'] = JSON.stringify(this.information_dialog_data.queries)
        }
        else if (this.deployment['mode'] == 'PRO') {
          payload['code'] = this.information_dialog_data.code
        }
        if (this.deployment['mode'] == 'INBENTA') {
          payload['products'] = []
          for (const i of this.information_dialog_data.products) payload['products'].push(this.deployment['products_schema'][i])
          payload['schema'] = this.information_dialog_data.schema
        }
        // Add deployment to the DB
        axios.put(path, payload)
        .then((response) => {
          const data = response.data.data
          this.notification(response.data.message, 'success')
          // Refresh user coins
          if ('coins' in data) this.$store.dispatch('coins', data['coins'])
          // Clear current deployment
          this.clear()
          // Refresh the deployment
          this.deployment['execution_id'] = data['execution_id']
          this.getDeployment()
          // Hide the Information dialog
          this.information_dialog = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
      },
      // -------------------------------------
      // QUERY
      // -------------------------------------
      newQuery() {
        this.query_dialog_mode = 'new'
        this.query_dialog_item = ''
        this.query_dialog_title = 'New Query'
        this.query_dialog = true
      },
      editQuery () {
        this.query_dialog_mode = 'edit'
        this.query_dialog_item = this.information_dialog_query_selected[0]['query']
        this.query_dialog_title = 'Edit Query'
        this.query_dialog = true
      },
      deleteQuery() {
        this.query_dialog_mode = 'delete'
        this.query_dialog_title = 'Delete Query'
        this.query_dialog = true
      },
      queryActionConfirm() {
        if (this.query_dialog_mode == 'new') this.newQueryConfirm()
        else if (this.query_dialog_mode == 'edit') this.editQueryConfirm()
        else if (this.query_dialog_mode == 'delete') this.deleteQueryConfirm()
      },
      newQueryConfirm() {
        // Check if all fields are filled
        if (!this.$refs.query_form.validate()) {
          this.notification('Please fill the required fields', 'error')
          return
        }
        // Check if new item already exists
        for (var i = 0; i < this.information_dialog_data.queries.length; ++i) {
          if (this.information_dialog_data.queries[i]['query'] == this.query_dialog_item) {
            this.notification('Query currently exists', 'error')
            return
          }
        }
        // Add item in the data table
        this.information_dialog_data.queries.push({'query': this.query_dialog_item})
        this.information_dialog_query_selected = []
        this.query_dialog = false
        this.notification('Query added successfully', 'success')
      },
      editQueryConfirm() {
        // Get Item Position
        for (var i = 0; i < this.information_dialog_data.queries.length; ++i) {
          if (this.information_dialog_data.queries[i]['query'] == this.information_dialog_query_selected[0]['query']) break
        }
        // Check if edited item already exists
        for (var j = 0; j < this.information_dialog_data.queries.length; ++j) {
          if (this.information_dialog_data.queries[j]['query'] == this.query_dialog_item && this.query_dialog_item != this.information_dialog_query_selected[0]['query']) {
            this.notification('Query currently exists', 'error')
            return
          }
        }
        // Edit item in the data table
        this.information_dialog_data.queries.splice(i, 1, {'query': this.query_dialog_item})
        this.information_dialog_query_selected = []
        this.query_dialog = false
        this.notification('Query edited successfully', 'success')
      },
      deleteQueryConfirm() {
        while(this.information_dialog_query_selected.length > 0) {
          var s = this.information_dialog_query_selected.pop()
          for (var i = 0; i < this.information_dialog_data.queries.length; ++i) {
            if (this.information_dialog_data.queries[i]['query'] == s['query']) {
              // Delete Item
              this.information_dialog_data.queries.splice(i, 1)
              break
            }
          }
        }
        this.notification('Selected queries removed successfully', 'success')
        this.query_dialog = false
      },
      // -------------------------------------
      // SHARE RESULTS
      // -------------------------------------
      resultsClipboard() {
        const el = document.createElement('textarea');    // Create a <textarea> element
        el.value = this.url + "/results/" + this.deployment['uri']; // Set its value to the string that you want copied
        el.setAttribute('readonly', '');                // Make it readonly to be tamper-proof
        el.style.position = 'absolute';                 
        el.style.left = '-9999px';                      // Move outside the screen to make it invisible
        document.body.appendChild(el);                  // Append the <textarea> element to the HTML document
        const selected =            
          document.getSelection().rangeCount > 0        // Check if there is any content selected previously
            ? document.getSelection().getRangeAt(0)     // Store selection if found
            : false;                                    // Mark as false to know no selection existed before
        el.select();                                    // Select the <textarea> content
        document.execCommand('copy');                   // Copy - only works as a result of a user action (e.g. click events)
        document.body.removeChild(el);                  // Remove the <textarea> element
        if (selected) {                                 // If a selection existed before copying
          document.getSelection().removeAllRanges();    // Unselect everything on the HTML document
          document.getSelection().addRange(selected);   // Restore the original selection
        }
        this.notification('Deployment URL added to the clipboard', 'info')
      },
      resultsShare() {
        // Build parameters
        const path = '/deployments/' + this.deployment['mode'].toLowerCase() +  '/public'
        const payload = {
          execution_id: this.deployment['execution_id'],
          public: !this.deployment['public']
        }
        axios.post(path, payload)
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
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
      },
      // -------------------------------------
      // AUXILIARY METHODS
      // -------------------------------------
      selectRow(id) {
        if (id == this.deployment['execution_id']) return '#616161'
        else return '#424242'
      },
      getMethodColor (method) {
        if (method == 'DEPLOY') return '#f44336'
        else if (method == 'TEST') return '#ff9800'
        else if (method == 'VALIDATE') return '#4caf50'
      },
      getModeColor (mode) {
        if (mode == 'BASIC') return '#67809f'
        else if (mode == 'PRO') return '#22313f'
      },
      regionColor (index, region) {
        if (index != 0) return ''
        if (region.startsWith('100%')) return 'background-color: #4caf50'
        else return 'background-color: #fb8c00'
      },
      regionIcon (progress) {
        if (progress.startsWith('100%')) return 'fas fa-check'
        else return 'fas fa-spinner'  
      },
      serverColor (progress) {
        if (progress.startsWith('100%')) return 'success--text'
        else return 'warning--text'
      },
      notification(message, color) {
        this.snackbarText = message
        this.snackbarColor = color 
        this.snackbar = true
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
        requestAnimationFrame(() => {
          if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
          if (typeof this.$refs.query_form !== 'undefined') this.$refs.query_form.resetValidation()
        })
      }
    }
  }
</script>