<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">INFORMATION</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>

        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text title="Show Parameters" @click="parameters()"><v-icon small style="padding-right:10px">fas fa-cog</v-icon>PARAMETERS</v-btn>
          <v-btn text title="Re-Deploy with other parameters" @click="redeploy()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>RE-DEPLOY</v-btn>
          <v-btn text title="Select Execution" @click="select()"><v-icon small style="padding-right:10px">fas fa-mouse-pointer</v-icon>SELECT</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn :disabled="start_execution" v-if="deployment['status'] == 'CREATED' && deployment['start_execution'] == 0" text title="Start Execution" @click="start()"><v-icon small style="padding-right:10px">fas fa-rocket</v-icon>START</v-btn>
          <v-btn :disabled="stop_execution" v-if="deployment['status'] == 'IN PROGRESS'" text title="Stop Execution" @click="stop()"><v-icon small style="padding-right:10px">fas fa-ban</v-icon>STOP</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        
        <div v-if="stop_execution" class="subtitle-1" style="margin-left:5px;">Stopping the execution...</div>
        <div v-else-if="deployment['status'] == 'IN PROGRESS' || start_execution" class="subtitle-1" style="margin-left:5px;">Starting the execution...</div>
        <v-progress-circular v-if="stop_execution || start_execution || deployment['status'] == 'IN PROGRESS'" :size="22" indeterminate color="white" width="2" style="margin-left:20px; margin-right:10px;"></v-progress-circular>

        <v-chip v-if="deployment['status'] == 'SUCCESS'" label color="success" style="margin-left:5px;">Execution Finished Successfully</v-chip>
        <v-chip v-else-if="deployment['status'] == 'WARNING'" label color="success" style="margin-left:5px;">Execution Finished with errors</v-chip>
        <v-chip v-else-if="deployment['status'] == 'FAILED'" label color="error" style="margin-left:5px;">Execution Failed</v-chip>

        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn v-if="deployment['results'] != null" text style="margin-left:15px;" title="Results"><v-icon small style="padding-right:10px;">fas fa-meteor</v-icon>RESULTS</v-btn>
          <v-btn v-if="deployment['logs'] != null" text title="Logs"><v-icon small style="padding-right:10px;">fas fa-scroll</v-icon>LOGS</v-btn>
        </v-toolbar-items>

        <v-spacer></v-spacer>
        <div class="subheading font-weight-regular" style="padding-right:20px;">Updated on <b>2019-07-25 12:10:08</b></div>
        <router-link class="nav-link" to="/deployments"><v-btn icon><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn></router-link>
      </v-toolbar>

      <!-- <v-progress-linear v-if="deployment['status'] == 'IN PROGRESS'" :indeterminate="true" height="5" color="info" style="margin:0px;" value="100"></v-progress-linear> -->

      <v-card-text>
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
              <v-icon v-else-if="props.item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
              <v-icon v-else-if="props.item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check-double</v-icon>
              <v-icon v-else-if="props.item.status == 'FAILED'" title="Failed" small style="color: #f44336; margin-left:11px;">fas fa-times</v-icon>
              <v-icon v-else-if="props.item.status == 'INTERRUPTED'" title="Interrupted" small style="color: #f44336; margin-left:13px;">fas fa-exclamation</v-icon>
            </template>
            <template v-slot:item.overall="props">
              <span></span>
            </template>
          </v-data-table>
        </v-card>

        <!-- VALIDATION -->
        <div class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">VALIDATION</div>
        <!-- validation -->
        <v-card style="margin-top:15px;">
          <v-data-table :headers="validation_headers" :items="validation_data" hide-default-footer>
            <template v-slot:item="props">
              <tr>
                <td class="success--text"><v-icon small color="success" style="margin-right:10px;">fas fa-check</v-icon><b>{{props.item.r1}}</b></td>
                <td class="warning--text"><v-icon small color="warning" style="margin-right:10px;">fas fa-spinner</v-icon><b>{{props.item.r2}}</b></td>
                <td class="warning--text"><v-icon small color="warning" style="margin-right:10px;">fas fa-spinner</v-icon><b>{{props.item.r3}}</b></td>
                <td class="error--text"><v-icon small color="error" style="margin-right:10px;">fas fa-times</v-icon><b>{{props.item.r4}}</b></td>
              </tr>
            </template>
          </v-data-table>
        </v-card>

        <!-- EXECUTION -->
        <div class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">EXECUTION</div>
        <v-card style="margin-top:15px;">
          <v-data-table :headers="execution_headers" :items="index(execution_data)" hide-default-footer>
            <template v-slot:item="props">
              <tr>
                <td v-if="props.item.index == 0" :style="`background-color:` + regionColor(props.item.r1)"><v-icon small style="margin-right:10px;">{{ regionIcon(props.item.r1) }}</v-icon><b>{{ props.item.r1 }}</b></td>
                <td v-if="props.item.index == 0" :style="`background-color:` + regionColor(props.item.r2)"><v-icon small style="margin-right:10px;">{{ regionIcon(props.item.r2) }}</v-icon><b>{{ props.item.r2 }}</b></td>
                <td v-if="props.item.index == 0" :style="`background-color:` + regionColor(props.item.r3)"><v-icon small style="margin-right:10px;">{{ regionIcon(props.item.r3) }}</v-icon><b>{{ props.item.r3 }}</b></td>
                <td v-if="props.item.index == 0" :style="`background-color:` + regionColor(props.item.r4)"><v-icon small style="margin-right:10px;">{{ regionIcon(props.item.r4) }}</v-icon><b>{{ props.item.r4 }}</b></td>

                <td v-if="props.item.index != 0" :class="serverColor(props.item.r1.progress)" style="padding-left:20px;">{{ props.item.r1.server }}. {{ props.item.r1.progress }}</td>
                <td v-if="props.item.index != 0" :class="serverColor(props.item.r2.progress)" style="padding-left:20px;">{{ props.item.r2.server }}. {{ props.item.r2.progress }}</td>
                <td v-if="props.item.index != 0" :class="serverColor(props.item.r3.progress)" style="padding-left:20px;">{{ props.item.r3.server }}. {{ props.item.r3.progress }}</td>
                <td v-if="props.item.index != 0" :class="serverColor(props.item.r4.progress)" style="padding-left:20px;">{{ props.item.r4.server }}. {{ props.item.r4.progress }}</td>
              </tr>
            </template>
          </v-data-table>
        </v-card>

        <!-- After Execution Headers -->
        <v-layout row wrap style="margin-top:15px; margin-left:0px; margin-right:0px;">
          <v-flex xs8>
            <div class="title font-weight-regular" style="padding-top:20px; padding-left:1px;">POST EXECUTION</div>
          </v-flex>
          <v-flex xs4>
            <div class="title font-weight-regular" style="padding-top:20px; padding-left:7px;">QUERIES</div>
          </v-flex>
        </v-layout>

        <!-- POST EXECUTION -->
        <v-layout row wrap style="margin-top:15px; margin-left:0px; margin-right:0px;">
          <!-- logs -->
          <v-flex xs4 style="padding-right:5px;">
            <v-card>
              <v-data-table :headers="logs_headers" :items="logs_data" hide-default-footer>
                <template v-slot:items="props">
                  <td>{{ props.item.status }}</td>
                </template>
              </v-data-table>
            </v-card>
          </v-flex>
          <!-- remaining-tasks -->
          <v-flex xs4 style="padding-left:5px; padding-right:5px;">
            <v-card>
              <v-data-table :headers="post_headers" :items="post_data" hide-default-footer>
                <template v-slot:items="props">
                  <td>{{ props.item.status }}</td>
                </template>
              </v-data-table>
            </v-card>
          </v-flex>
          <!-- queries -->
          <v-flex xs4 style="padding-left:5px;">
            <v-card>
              <v-data-table :headers="summary_headers" :items="summary_data" hide-default-footer>
                <template v-slot:items="props">
                  <td><b>{{ props.item.total }}</b></td>
                  <td><b>{{ props.item.succeeded }}</b></td>
                  <td><b>{{ props.item.failed }}</b></td>
                </template>
              </v-data-table>
            </v-card>
          </v-flex>
        </v-layout>

        <!-- ERROR -->
        <!-- <div class="title font-weight-regular" style="padding-top:20px; padding-left:1px; padding-bottom:20px;">ERROR</div>
        <v-card>
        </v-card> -->
      </v-card-text>
    </v-card>

    <v-dialog v-model="information_dialog" :persistent="information_dialog_mode == 're-deploy'" max-width="70%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ information_dialog_mode.toUpperCase() }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="information_dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12>
                <div class="title font-weight-regular" style="margin-bottom: 25px;">{{ this.deploymentMode }}</div>
                <v-text-field readonly v-model="information_dialog_data.name" label="Name" style="padding-top:0px;"></v-text-field>
                <v-select v-if="deploymentMode != 'PRO'" :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.environment" :items="[information_dialog_data.environment]" label="Environment" style="padding-top:0px;"></v-select>

                <v-text-field v-if="deploymentMode != 'PRO'" :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.databases" label="Databases" style="padding-top:0px;"></v-text-field>
                <v-card v-if="deploymentMode != 'PRO'" style="margin-bottom:20px;">
                  <v-toolbar flat dense color="#2e3131" style="margin-top:5px;">
                    <v-toolbar-title class="white--text">Queries</v-toolbar-title>
                    <v-divider v-if="information_dialog_mode == 're-deploy'" class="mx-3" inset vertical></v-divider>
                    <v-toolbar-items v-if="information_dialog_mode == 're-deploy'" class="hidden-sm-and-down" style="padding-left:0px;">
                      <v-btn text @click='newQuery()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                      <v-btn v-if="information_dialog_query_selected.length == 1" text @click="editQuery()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                      <v-btn v-if="information_dialog_query_selected.length > 0" text @click='deleteQuery()'><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                    </v-toolbar-items>
                  </v-toolbar>
                  <v-divider></v-divider>
                  <v-data-table v-model="information_dialog_query_selected" :headers="information_dialog_data.query_headers" :items="information_dialog_data.queries" item-key="query" :show-select="information_dialog_mode == 're-deploy'" hide-default-header hide-default-footer class="elevation-1">
                  </v-data-table>
                </v-card>

                <codemirror v-if="deploymentMode == 'PRO'" v-model="information_dialog_data.code" :options="cmOptions" style="margin-bottom:15px;"></codemirror>

                <div class="subtitle-1 font-weight-regular">METHOD</div>
                <v-radio-group :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.method" style="margin-top:10px;">
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

                <div class="subtitle-1 font-weight-regular" style="margin-top:-5px;">EXECUTION</div>
                <v-radio-group :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.execution" style="margin-top:10px;">
                  <v-radio color="primary" value="sequential">
                    <template v-slot:label>
                      <div>Sequential</div>
                    </template>
                  </v-radio>
                  <v-radio color="primary" value="parallel">
                    <template v-slot:label>
                      <div>Parallel</div>
                    </template>
                  </v-radio>
                </v-radio-group>

                <v-text-field :readonly="information_dialog_mode == 'parameters'" v-if="information_dialog_data.execution=='parallel'" v-model="information_dialog_data.threads" label="Threads" style="margin-top:0px; padding-top:0px;"></v-text-field>
                <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.start_execution" label="Start execution" color="primary" hide-details style="margin-top:-10px; margin-bottom:5px;"></v-checkbox>
              
                <v-divider v-if="information_dialog_mode == 're-deploy'" style="margin-top:15px;"></v-divider>

                <div v-if="information_dialog_mode == 're-deploy'" style="margin-top:20px;">
                  <v-btn color="success" @click="redeploySubmit()">RE-DEPLOY</v-btn>
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

    <v-dialog v-model="select_dialog" max-width="70%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">SELECT EXECUTION</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="select_dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12>
                <v-card>
                  <v-toolbar flat dense color="#2e3131">
                    <v-toolbar-title class="white--text">Executions</v-toolbar-title>
                  </v-toolbar>
                  <v-divider></v-divider>
                  <v-data-table :headers="executions.headers" :items="executions.items" item-key="id" hide-default-footer class="elevation-1">
                    <template v-slot:item="props">
                      <tr :style="`background-color:` + selectRow(props.item.id)">
                        <td>{{ props.item.environment }}</td>
                        <td><span :style="'color: ' + getMethodColor(props.item.method.toUpperCase())" style="font-weight:500">{{ props.item.method.toUpperCase() }}</span></td>
                        <td>{{ props.item.created }}</td>
                        <td>
                          <v-icon v-if="props.item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
                          <v-icon v-else-if="props.item.status == 'QUEUED'" title="Queued" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
                          <v-icon v-else-if="props.item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
                          <v-icon v-else-if="props.item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check-double</v-icon>
                          <v-icon v-else-if="props.item.status == 'FAILED'" title="Failed" small style="color: #f44336; margin-left:11px;">fas fa-times</v-icon>
                          <v-icon v-else-if="props.item.status == 'INTERRUPTED'" title="Interrupted" small style="color: #f44336; margin-left:13px;">fas fa-exclamation</v-icon>
                        </td>
                        <td>{{ props.item.started }}</td>
                        <td>{{ props.item.ended }}</td>
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
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 style="padding-bottom:10px">
                <div class="subtitle-1" style="padding-bottom:10px">{{ action_dialog_text }}</div>
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

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<style>
.CodeMirror {
  min-height:800px;
  font-size: 14px;
}
.CodeMirror pre {
  padding: 0 14px;
}
</style>

<script>
  import axios from 'axios'

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
  import 'codemirror/addon/search/searchcursor.js'
  import 'codemirror/addon/search/search.js'
  import 'codemirror/keymap/sublime.js'

  export default  {
    data: () => ({
      // Deployment Data
      deployment: {},

      // Deployment Executions
      executions: {},

      // Information Data Table
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

      // Init Code Parameters
      cmOptions: {
        readOnly: true,
        autoCloseBrackets: true,
        styleActiveLine: true,
        lineNumbers: true,
        line: true,
        mode: 'python',
        theme: 'monokai',
        keyMap: 'sublime',
        extraKeys: { "Tab": function(cm) { cm.replaceSelection("    " , "end"); }}
      },

      // Executions Flag
      stop_execution: false,
      start_execution: false,

      // ...

      databases: "db1, db2, db3",
      status_headers: [
        { text: 'Name', align: 'left', value: 'name', sortable: false },
        { text: 'Environment', value: 'environment', sortable: false },
        { text: 'Mode', align: 'left', value: 'mode', sortable: false },
        { text: 'Method', align: 'left', value: 'method', sortable: false },
        { text: 'Created', align: 'left', value: 'created', sortable: false },
        { text: 'Started', align: 'left', value: 'started', sortable: false },
        { text: 'Ended', align: 'left', value: 'ended', sortable: false },
        { text: 'Overall', align: 'left', value: 'overall', sortable: false }
      ],
      status_data: [
        {
          id: 1,
          name: 'Release 3.33.0',
          environment: 'Production',
          mode: "BASIC",
          method: 'DEPLOYMENT',
          created: '2019-07-07 07:00:00',
          started: '2019-07-07 08:00:00',
          ended: '2019-07-07 08:12:15',
          overall: '00:12:10'
        }
      ],
      validation_headers: [
        { text: 'AWS-EU', align:'left', value: 'r1', sortable: false },
        { text: 'AWS-US', align:'left', value: 'r2', sortable: false },
        { text: 'AWS-BR', align:'left', value: 'r3', sortable: false },
        { text: 'AWS-JP', align:'left', value: 'r4', sortable: false }
      ],
      validation_data: [
        { 
          r1: "SUCCEEDED",
          r2: "VALIDATING",
          r3: "VALIDATING",
          r4: "FAILED"
        }
      ],
      execution_headers: [
        { text: 'AWS-EU', align:'left', value: 'r1', sortable: false },
        { text: 'AWS-US', align:'left', value: 'r2', sortable: false },
        { text: 'AWS-BR', align:'left', value: 'r3', sortable: false },
        { text: 'AWS-JP', align:'left', value: 'r4', sortable: false }
      ],
      execution_data: [
        { r1: "100% (143/143 DBs)", r2: "56% (756/1362 DBs)", r3: "82% (1467/1739 DBs)", r4: "100% (253/253 DBs)" },
        { r1: { server: "awseu-sql01", progress: "100% (21/21 DBs)" }, r2: { server: "aws-sql01", progress: "52% (12/21 DBs)" }, r3: { server: "awsbr-sql01", progress: "52% (12/21 DBs)" }, r4: { server: "awsjp-sql01", progress: "100% (153/153 DBs)" }},
        { r1: { server: "awseu-sql02", progress: "100% (122/122 DBs)" }, r2: { server: "aws-sql02", progress: "43% (108/211 DBs)" }, r3: { server: "awsbr-sql02", progress: "8% (2/12 DBs)" }, r4: { server: "awsjp-sql02", progress: "100% (100/100 DBs)" }}
      ],
      logs_headers: [
        { text: 'LOGS', align:'left', value: 'status', sortable: false }
      ],
      logs_data: [
        { status: "Compressing Logs From Remote Hosts..." },
        { status: "Downloading Logs From Remote Hosts..." },
        { status: "Merging 'AWS-EU'..." },
        { status: "Merging 'AWS-JP'..." },
        { status: "Merging 'AWS-US'..." },
        { status: "Merging 'AWS-BR'..." },
        { status: "Generating a Single Log File..." }
      ],
      post_headers: [
        { text: 'REMAINING TASKS', align:'left', value: 'status', sortable: false }
      ],
      post_data: [
        { status: "Uploading Logs to Amazon S3 Bucket 'meteor'..." },
        { status: "Cleaning Remote Environments..." },
        { status: "Cleaning Local Environments..." },
        { status: "Cleaning Remaining Processes..." },
        { status: "Sending Slack Message to #meteor..." }
      ],
      summary_headers: [
        { text: 'TOTAL', align:'left', value: 'total', sortable: false },
        { text: 'SUCCEEDED', align:'left', value: 'succeeded', sortable: false },
        { text: 'FAILED', align:'left', value: 'failed', sortable: false }
      ],
      summary_data: [
        { 
          total: "2037",
          succeeded: "2037 (100.0%)",
          failed: "0 (0.0%)"
        }
      ],
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: ''
    }),
    components: { codemirror },
    props: ['deploymentID', 'deploymentMode'],
    created() {
      if (typeof this.deploymentID === "undefined") this.$router.push('/deployments')
      else if (this.deploymentMode == 'BASIC') this.getDeploymentBasic()
      else if (this.deploymentMode == 'PRO') this.getDeploymentPro()
    },
    methods: {
      // -------------
      // BASE METHODS
      // -------------
      getDeploymentBasic() {
        // Get Deployment Data
        const path = this.$store.getters.url + '/deployments/basic'
        axios.get(path, { params: { deploymentID: this.deploymentID } })
          .then((response) => {
            const data = response.data.data[0]
            this.parseRequest(data)
          })
          .catch((error) => {
            if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            // eslint-disable-next-line
            console.error(error)
          })
      },
      getDeploymentPro() {
        // Get Deployment Data
        const path = this.$store.getters.url + '/deployments/pro'
        axios.get(path, { params: { deploymentID: this.deploymentID } })
          .then((response) => {
            const data = response.data.data[0]
            this.parseRequest(data)
          })
          .catch((error) => {
            if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            // eslint-disable-next-line
            console.error(error)
          })
      },
      parseRequest(data) {
        this.deployment['id'] = data['id']
        this.deployment['execution_id'] = data['execution_id']
        this.deployment['mode'] = data['mode']
        this.deployment['name'] = data['name']
        this.deployment['environment'] = data['environment']
        if (this.deployment['mode'] == 'BASIC') {
          this.deployment['databases'] = data['databases']
          this.deployment['queries'] = []
          var queries = JSON.parse(data['queries'])
          for (var i in queries) this.deployment['queries'].push(queries[i])
          this.deployment['query_headers'] = [{text: 'Query', value: 'query'}]
        }
        else if (this.deployment['mode'] == 'PRO') {
          this.deployment['code'] = data['code']
        }
        this.deployment['method'] = data['method'].toLowerCase()
        this.deployment['execution'] = data['execution'].toLowerCase()
        this.deployment['threads'] = data['execution_threads']
        this.deployment['start_execution'] = data['start_execution']
        this.deployment['created'] = data['created']
        this.deployment['started'] = data['started']
        this.deployment['ended'] = data['ended']
        this.deployment['status'] = data['status']
        this.deployment['results'] = data['results']
        this.deployment['logs'] = data['logs']

        // Add Deployment to the information table
        this.information_items = []
        this.information_items.push(this.deployment)

        // Get Executions
        this.getExecutions()
      },
      getExecutions() {
        // Get Deployment Executions
        const path = this.$store.getters.url + '/deployments/' + this.deployment['mode'].toLowerCase() + '/executions'
        axios.get(path, { params: { deploymentID: this.deploymentID } })
          .then((response) => {
            this.executions['items'] = response.data.data
            this.executions['headers'] = [
              { text: 'Environment', value: 'environment' },
              { text: 'Method', value: 'method' },
              { text: 'Created', value: 'created' },
              { text: 'Status', value: 'status' },
              { text: 'Started', value: 'started' },
              { text: 'Ended', value: 'ended' },
              { text: 'Actions', value: 'actions' }
            ]
          })
          .catch((error) => {
            if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            // eslint-disable-next-line
            console.error(error)
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
      redeploy() {
        this.information_dialog_mode = 're-deploy'
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
        this.notification('Starting the execution. Please wait...', 'primary')
        this.start_execution = true
        this.action_dialog = false
      },
      actionSubmitStop() {
        this.notification('Stopping the execution. Please wait...', 'primary')
        this.stop_execution = true
        this.action_dialog = false
      },
      // ------------------------
      // SELECT EXECUTION DIALOG
      // ------------------------
      selectExecution(execution_id) {
        // Get Execution
        const path = this.$store.getters.url + '/deployments/' + this.deployment['mode'].toLowerCase() + '/execution'
        axios.get(path, { params: { executionID: execution_id } })
          .then((response) => {
            const data = response.data.data[0]
            this.parseRequest(data)
            this.select_dialog = false
          })
          .catch((error) => {
            if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            // eslint-disable-next-line
            console.error(error)
          })
      },
      // -------------------------------------
      // RE-DEPLOY
      // -------------------------------------
      redeploySubmit() {
        // Build parameters
        const path = this.$store.getters.url + '/deployments/' + this.deployment['mode'].toLowerCase()
        var payload = {
          id: this.information_dialog_data.id,
          name: this.deployment.name,
          environment: this.information_dialog_data.environment,
          mode: this.deployment['mode'].toUpperCase(),
          method: this.information_dialog_data.method.toUpperCase(),
          execution: this.information_dialog_data.execution.toUpperCase(),
          execution_threads: this.information_dialog_data.threads,
          start_execution: this.information_dialog_data.start_execution
        }
        // Build different modes
        if (this.deployment['mode'] == 'BASIC') {
          payload['databases'] = this.information_dialog_data.databases
          payload['queries'] = JSON.stringify(this.information_dialog_data.queries)
        }
        else if (this.deployment['mode'] == 'PRO') {
          payload['code'] = this.information_dialog_data.code
        }
        // Add deployment to the DB
        axios.put(path, payload)
        .then((response) => {
          this.notification(response.data.message, 'success')
          // Refresh the deployments
          if (this.deploymentMode == 'BASIC') this.getDeploymentBasic()
          else if (this.deploymentMode == 'PRO') this.getDeploymentPro()
          // Hide the Information dialog
          this.information_dialog = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
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
      regionColor (progress) {
        if (progress.startsWith('100%')) return '#4caf50'
        else return '#fb8c00'
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
          index: index,
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