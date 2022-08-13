<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">EXECUTION</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn v-if="'status' in deployment" text title="Show Execution Parameters" @click="parameters()"><v-icon small style="margin-right:10px">fas fa-cog</v-icon>PARAMETERS</v-btn>
          <v-btn v-if="'status' in deployment" text title="Select Execution" @click="select()"><v-icon small style="margin-right:10px">fas fa-mouse-pointer</v-icon>EXECUTIONS</v-btn>
          <v-btn v-if="'status' in deployment" :disabled="!deployment.owner || ['STARTING','IN PROGRESS','STOPPING','QUEUED'].includes(deployment['status'])" text :title="(deployment['status'] == 'CREATED' || deployment['status'] == 'SCHEDULED') ? 'Edit Execution' : 'Re-Deploy Execution'" @click="edit()"><v-icon small style="margin-right:10px">fas fa-meteor</v-icon>{{(deployment['status'] == 'CREATED' || deployment['status'] == 'SCHEDULED') ? 'EDIT' : 'RE-DEPLOY'}}</v-btn>
          <v-btn v-if="'status' in deployment" :disabled="!deployment.owner" text title="Share Deployment" @click="shareDeploymentDialog = true" style="height:100%"><v-icon small style="margin-right:10px;">fas fa-share</v-icon>SHARE</v-btn>
          <v-divider v-if="['CREATED','SCHEDULED','QUEUED','STARTING','IN PROGRESS','STOPPING'].includes(deployment['status'])" class="mx-3" inset vertical></v-divider>
          <v-btn :disabled="!deployment.owner || start_execution" v-if="['CREATED','SCHEDULED'].includes(deployment['status'])" text title="Start Execution" @click="start()"><v-icon small style="margin-right:10px">fas fa-play</v-icon>START</v-btn>
          <v-btn v-if="['QUEUED','STARTING','IN PROGRESS','STOPPING'].includes(deployment['status'])" :disabled="!deployment.owner || deployment['status'] == 'STARTING' || (deployment['status'] == 'STOPPING' && deployment['stopped'] == 'forceful')" text title="Stop Execution" @click="stop()"><v-icon small style="margin-right:10px">fas fa-ban</v-icon>STOP</v-btn>
        </v-toolbar-items>
        <v-divider v-if="'status' in deployment" class="mx-3" inset vertical></v-divider>
        
        <div v-if="(stop_execution && deployment['status'] != 'STOPPED') || deployment['status'] == 'STOPPING'" class="subtitle-1" style="margin-left:5px;">Stopping the execution...</div>
        <div v-else-if="(start_execution && deployment['status'] == 'IN PROGRESS') || deployment['status'] == 'IN PROGRESS'" class="subtitle-1" style="margin-left:5px;">Execution in progress...</div>
        <div v-else-if="deployment['status'] == 'QUEUED'" class="subtitle-1" style="margin-left:5px;">Queue Position: <b>{{ information_items[0]['queue'] }}</b></div>
        <div v-else-if="start_execution || deployment['status'] == 'STARTING'" class="subtitle-1" style="margin-left:5px;">Starting the execution...</div>
        <v-progress-circular v-if="start_execution || (stop_execution && deployment['status'] != 'STOPPED') || deployment['status'] == 'QUEUED' || deployment['status'] == 'STARTING' || deployment['status'] == 'STOPPING' ||  deployment['status'] == 'IN PROGRESS'" :size="22" indeterminate color="white" width="2" style="margin-left:20px; margin-right:20px;"></v-progress-circular>

        <v-chip v-if="deployment['status'] == 'SUCCESS'" label color="#00b16a" style="font-weight:500; margin-left:5px; margin-right:5px;" title="The execution finished successfully">SUCCESS</v-chip>
        <v-chip v-else-if="deployment['status'] == 'WARNING'" label color="#ff9800" style="font-weight:500; margin-left:5px; margin-right:5px;" title="Some queries failed">WARNING</v-chip>
        <v-chip v-else-if="deployment['status'] == 'FAILED'" label color="#EF5354" style="font-weight:500; margin-left:5px; margin-right:5px;" title="An error has occurred during the execution">FAILED</v-chip>
        <v-chip v-else-if="deployment['status'] == 'STOPPED'" label color="#EF5354" style="font-weight:500; margin-left:5px; margin-right:5px;" title="The execution has been interrupted">STOPPED</v-chip>
        <v-divider v-if="['SUCCESS','WARNING','FAILED','STOPPED'].includes(deployment['status'])" class="mx-3" inset vertical></v-divider>

        <v-toolbar-items>
          <v-btn v-if="show_results" text title="Show Execution Progress" @click="show_results = false" style="height:100%"><v-icon small style="margin-right:10px;">fas fa-spinner</v-icon>PROGRESS</v-btn>
          <div v-if="deployment['method'] != 'validate' && (deployment['status'] == 'SUCCESS' || deployment['status'] == 'WARNING' || (deployment['status'] == 'FAILED' && !validation_error) || (deployment['status'] == 'STOPPED' && deployment['uri'] != null)) && ('progress' in deployment && 'queries' in deployment['progress'] && 'total' in deployment['progress']['queries'] && deployment['progress']['queries']['total'] > 0)">
            <v-btn v-if="!show_results" text title="Show Execution Results" @click="showResults()" style="height:100%"><v-icon small style="margin-right:10px;">fas fa-bars</v-icon>RESULTS</v-btn>
          </div>
        </v-toolbar-items>

        <v-spacer></v-spacer>
        <div v-if="last_updated != ''" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(last_updated) }}</b></div>
        <v-divider class="ml-3 mr-1" inset vertical></v-divider>
        <v-btn icon @click="goBack()"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>

      <!-- RESULTS -->
      <v-card-text v-if="show_results" style="padding:0px; background-color:rgb(55, 53, 64); height:calc(100vh - 180px)">
        <Results :src="deployment['uri']" :height="`calc(100vh - 181px)`"></Results>
      </v-card-text>

      <v-card-text v-else>
        <!-- INFORMATION -->
        <v-card>
          <v-data-table :loading="loading" :headers="information_headers" :items="information_items" hide-default-footer class="elevation-1" mobile-breakpoint="0">
            <template v-slot:[`item.environment`]="{ item }">
              <span :title="item.environment.shared ? (item.environment.secured ? 'Shared (Secured)' : 'Shared') : (item.environment.secured ? 'Personal (Secured)' : 'Personal')">{{ item.environment.name }}</span>
            </template>
            <template v-slot:[`item.mode`]="{ item }">
              <v-icon small :title="item.mode.charAt(0).toUpperCase() + item.mode.slice(1).toLowerCase()" :color="getModeColor(item.mode)" :style="`text-transform:capitalize; margin-left:${item.mode == 'BASIC' ? '8px' : '6px'}`">{{ item.mode == 'BASIC' ? 'fas fa-chess-knight' : 'fas fa-chess-queen' }}</v-icon>
            </template>
            <template v-slot:[`item.method`]="{ item }">
              <span :style="'color: ' + getMethodColor(item.method.toUpperCase())">{{ item.method.toUpperCase() }}</span>
            </template>
            <template v-slot:[`item.status`]="{ item }">
              <v-icon v-if="item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
              <v-icon v-else-if="item.status == 'SCHEDULED'" :title="parseSchedule(deployment['schedule_type'], dateFormat(deployment['scheduled']))" small style="color: #ff9800; margin-left:8px;">fas fa-clock</v-icon>
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
        <div v-if="validation_items.length > 0 && Object.keys(validation_items[0]).length != 0" class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">VALIDATION</div>
        <!-- validation -->
        <v-card v-if="validation_items.length > 0 && Object.keys(validation_items[0]).length != 0" style="margin-top:15px;">
          <v-data-table :headers="validation_headers" :items="validation_items" hide-default-footer mobile-breakpoint="0">
            <template v-for="header in validation_headers" v-slot:[`header.${header.value}`]>
              <div :key="header.value">
                <v-icon size="14" :title="header.shared ? 'Shared' : 'Personal'" :color="header.shared ? '#EB5F5D' : 'warning'" style="margin-right:8px; margin-bottom:2px">{{ header.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                {{ header.text }}
              </div>
            </template>
            <template v-slot:item="">
              <tr>
                <td v-for="item in validation_headers" :key="item.value">
                  <span v-if="validation_items[0][item.value] == 'VALIDATING'" class="warning--text"><v-icon small color="warning" style="margin-right:10px;">fas fa-spinner</v-icon><b>{{ validation_items[0][item.value] }}</b></span>
                  <span v-else-if="validation_items[0][item.value] == 'SUCCEEDED'" style="color:#00b16a;"><v-icon small color="#00b16a" style="margin-right:10px;">fas fa-check</v-icon><b>{{ validation_items[0][item.value] }}</b></span>
                  <span v-else-if="validation_items[0][item.value] == 'FAILED'" class="error--text"><v-icon small color="#EF5354" style="margin-right:10px;">fas fa-times</v-icon><b>{{ validation_items[0][item.value] }}</b></span>
                </td>
              </tr>
            </template>
          </v-data-table>
        </v-card>

        <!-- VALIDATION - ERROR -->
        <div v-if="validation_items.length > 0 && validation_error" class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">ERROR</div>
        <v-card v-if="validation_items.length > 0 && validation_error" style="margin-top:15px;">
          <v-card-text style="padding:10px 15px 10px 17px;">
            <v-container style="padding:0px!important; margin:0px!important;">
              <v-layout wrap>
                <v-flex xs12>
                  <div v-for="region in Object.values(deployment['progress']['validation'])" :key="region.id">
                    <div v-if="!region.success">
                      <div v-if="'error' in region || 'errors' in region" class="subtitle-1 font-weight-medium warning--text">
                        <v-icon size="14" :title="region.shared ? 'Shared' : 'Personal'" :color="region.shared ? '#EB5F5D' : 'warning'" style="margin-right:5px; margin-bottom:2px">{{ region.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                        {{ region.name }}
                      </div>
                      <div v-if="'error' in region" class="body-1 font-weight-regular">{{ region.error }}</div>
                      <div v-for="server in region.errors" :key="server.id">
                        <div class="body-1 font-weight-regular"><span style="font-weight:500">- {{ server['name'] }}.</span> {{ server['error'] }} </div>
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
          <v-data-table :headers="execution_headers" :items="this.index(execution_summary)" hide-default-footer mobile-breakpoint="0">
            <template v-for="header in execution_headers" v-slot:[`header.${header.value}`]>
              <div :key="header.value">
                <!-- <v-icon size="14" :title="header.shared ? 'Shared' : 'Personal'" :color="header.shared ? '#EB5F5D' : 'warning'" style="margin-right:8px; margin-bottom:2px">{{ header.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon> -->
                {{ header.text }}
              </div>
            </template>
            <template v-slot:item="">
              <tr>
                <td v-for="item in Object.values(execution_headers)" :key="item.value" :style="regionColor(execution_summary[0][item.value]) + `width: ${100/execution_headers.length}%`">
                  <span><v-icon small style="margin-right:10px;">{{ regionIcon(execution_summary[0][item.value]) }}</v-icon><span style="font-weight:700">{{ execution_summary[0][item.value] === undefined ? 'Initiating...' : execution_summary[0][item.value] }}</span></span>
                </td>
             </tr>
            </template>
          </v-data-table>
          <!-- Servers -->
          <v-data-table v-if="execution_items.length > 0" :headers="execution_headers" :items="this.index(execution_items)" hide-default-header :hide-default-footer="execution_items.length < 11" mobile-breakpoint="0">
            <template v-slot:item="props">
              <tr>
                <td v-for="item in Object.values(execution_headers)" :key="item.value" :style="`width: ${100/execution_headers.length}%`">
                  <div v-if="item.value in execution_items[props.item.i]">
                    <v-icon size="14" :title="execution_items[props.item.i][item.value].shared ? 'Shared' : 'Personal'" :color="execution_items[props.item.i][item.value].shared ? '#EB5F5D' : 'warning'" style="margin-right:10px; margin-bottom:1px">{{ execution_items[props.item.i][item.value].shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                    <span :style="serverColor(execution_items[props.item.i][item.value]['progress'])"><span style="font-weight:700">{{ execution_items[props.item.i][item.value]['server'] }}</span> {{ execution_items[props.item.i][item.value]['progress'] }}</span>
                  </div>
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
        <v-layout v-if="logs_data.length > 0 || tasks_data.length > 0" row wrap style="margin-top:15px; margin-left:0px; margin-right:0px; margin-bottom:0px">
          <!-- logs -->
          <v-flex v-if="logs_data.length > 0" xs4 style="padding-right:5px;">
            <v-card>
              <v-data-table :headers="logs_headers" :items="logs_data" hide-default-footer mobile-breakpoint="0">
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
              <v-data-table :headers="tasks_headers" :items="tasks_data" hide-default-footer mobile-breakpoint="0">
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
              <v-data-table :headers="queries_headers" :items="queries_data" hide-default-footer mobile-breakpoint="0">
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
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form">
                  <v-autocomplete :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.environment" :items="information_dialog_mode == 'parameters' ? [information_dialog_data.environment] : environments" item-value="id" return-object item-text="name" label="Environment" :rules="[v => !!v || '']" required>
                    <template v-slot:item="{ item }" >
                      <v-row align="center" no-gutters>
                        <v-col class="flex-grow-1 flex-shrink-1">
                          {{ item.name }}
                        </v-col>
                        <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
                          <v-chip label>
                            <v-icon small :color="item.shared ? '#EF5354' : 'warning'" :style="`${item.secured ? 'margin-right:2px' : 'margin-right:8px'}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                            <v-icon v-if="item.secured" title="Secured" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-top:4px; padding-right:8px">fas fa-lock</v-icon>
                            {{ item.shared ? 'Shared' : 'Personal' }}
                            </v-chip>
                        </v-col>
                      </v-row>
                    </template>
                    <template v-slot:selection="{ item }" >
                      <v-icon small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? '#EF5354' : 'warning'" :style="`${item.secured ? 'margin-right:2px' : 'margin-right:8px'}; cursor:default`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                      <v-icon v-if="item.secured" title="Secured" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-top:4px; padding-right:8px; cursor:default">fas fa-lock</v-icon>
                      <span style="margin-right:5px">{{ item.name }}</span>
                    </template>
                  </v-autocomplete>
                  <v-text-field v-if="information_dialog_execution_mode == 'BASIC'" :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.databases" label="Databases" hint="Separated by commas. Wildcards allowed: % _" :rules="[v => !!v || '']" style="padding-top:0px;"></v-text-field>
                  <v-card v-if="information_dialog_execution_mode == 'BASIC'" style="margin-bottom:20px;">
                    <v-toolbar flat dense color="#2e3131" style="margin-top:5px;">
                      <v-toolbar-title class="white--text subtitle-1">QUERIES</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-toolbar-items v-if="information_dialog_mode != 'parameters'" style="padding-left:0px;">
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
                      <v-toolbar-items v-else style="padding-left:0px;">
                        <v-btn :disabled="information_dialog_query_selected.length == 0" text @click='showQuery()'><v-icon small style="margin-right:10px">fas fa-bookmark</v-icon>DETAILS</v-btn>
                      </v-toolbar-items>
                    </v-toolbar>
                    <v-divider></v-divider>
                    <v-data-table v-model="information_dialog_query_selected" :headers="information_dialog_data.query_headers" :items="information_dialog_data.queries" item-key="id" show-select :hide-default-header="typeof information_dialog_data.queries === 'undefined' || information_dialog_data.queries.length == 0" :hide-default-footer="typeof information_dialog_data.queries === 'undefined' || information_dialog_data.queries.length < 11" class="elevation-1" mobile-breakpoint="0">
                      <template v-ripple v-slot:[`header.data-table-select`]="{}">
                        <v-simple-checkbox
                          :value="information_dialog_data.queries.length == 0 ? false : information_dialog_query_selected.length == information_dialog_data.queries.length"
                          :indeterminate="information_dialog_query_selected.length > 0 && information_dialog_query_selected.length != information_dialog_data.queries.length"
                          @click="information_dialog_query_selected.length == information_dialog_data.queries.length ? information_dialog_query_selected = [] : information_dialog_query_selected = [...information_dialog_data.queries]">
                        </v-simple-checkbox>
                      </template>
                      <template v-slot:[`item.query`]="{ item }">
                        <td style="padding-top:5px; padding-bottom:5px">{{ item.query }}</td>
                      </template>
                    </v-data-table>
                  </v-card>
                  <div v-if="information_dialog_execution_mode == 'PRO'" style="margin-top:-5px; margin-bottom:10px;">
                    <v-tooltip right>
                      <template v-slot:activator="{ on }">
                        <span v-on="on" class="subtitle-1 font-weight-regular white--text">
                          CODE
                          <v-icon small style="margin-left:5px; margin-bottom:4px;">fas fa-question-circle</v-icon>
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
                          <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                        </span>
                      </template>
                      <span>
                        <b style="color:#00b16a">VALIDATE</b> Tests all server connections.
                        <br>
                        <b class="orange--text">TEST</b> A simulation is performed (only SELECTs & SHOWs are executed).
                        <br>
                        <b style="color:#EF5354">DEPLOY</b> Executes ALL queries.
                      </span>
                    </v-tooltip>
                  </div>
                  <v-radio-group :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.method" hide-details style="margin-top:10px">
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
                  <!-- SCHEDULE -->
                  <div style="margin-top:15px">
                    <v-tooltip right>
                      <template v-slot:activator="{ on }">
                        <span v-on="on" class="subtitle-1 font-weight-regular white--text">
                          SCHEDULE
                          <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                        </span>
                      </template>
                      <span>Enable this option to decide when the deployment should be executed.</span>
                    </v-tooltip>
                  </div>
                  <v-switch :readonly="information_dialog_mode == 'parameters'" :disabled="loading" v-model="schedule_enabled" label="Schedule execution" color="info" hide-details style="margin-top:15px; padding:0px"></v-switch>
                  <div v-if="schedule_enabled" style="margin-top:15px">
                    <span class="body-1 font-weight-light white--text">Select the schedule type.</span>
                    <v-radio-group :readonly="information_dialog_mode == 'parameters'" row v-model="information_dialog_data.schedule_type" style="margin-top:10px; margin-bottom:15px" hide-details>
                      <v-radio value="one_time">
                        <template v-slot:label>
                          <div class="white--text">One time</div>
                        </template>
                      </v-radio>
                      <v-radio value="daily">
                        <template v-slot:label>
                          <div class="white--text">Daily</div>
                        </template>
                      </v-radio>
                      <v-radio value="weekly">
                        <template v-slot:label>
                          <div class="white--text">Weekly</div>
                        </template>
                      </v-radio>
                      <v-radio value="monthly">
                        <template v-slot:label>
                          <div class="white--text">Monthly</div>
                        </template>
                      </v-radio>
                    </v-radio-group>
                    <span class="body-1 font-weight-light white--text">Select the execution time.</span>
                    <div @click="schedule_change">
                      <v-text-field :readonly="information_dialog_mode == 'parameters'" ref="schedule_datetime" filled v-model="schedule_datetime" label="Execution time" :rules="[v => !!v || '']" required hide-details style="margin-top:15px; margin-bottom:5px"></v-text-field>
                    </div>
                    <div v-show="information_dialog_data.schedule_type == 'weekly'" style="margin-top:15px">
                      <span class="body-1 font-weight-light white--text">Select what days of the week the schedule should execute.</span>
                      <v-row no-gutters>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_week" label="Monday" value="1" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_week" label="Tuesday" value="2" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_week" label="Wednesday" value="3" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                      </v-row>
                      <v-row no-gutters>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_week" label="Thursday" value="4" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_week" label="Friday" value="5" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_week" label="Saturday" value="6" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                      </v-row>
                      <v-row no-gutters style="margin-bottom:5px">
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_week" label="Sunday" value="7" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                      </v-row>
                    </div>
                    <div v-show="information_dialog_data.schedule_type == 'monthly'" style="margin-top:15px">
                      <span class="body-1 font-weight-light white--text">Select what months the schedule should execute.</span>
                      <v-row no-gutters>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="January" value="1" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="February" value="2" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="March" value="3" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="April" value="4" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                      </v-row>
                      <v-row no-gutters>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="May" value="5" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="June" value="6" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="July" value="7" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="August" value="8" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                      </v-row>
                      <v-row no-gutters style="margin-bottom:15px">
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="September" value="9" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="October" value="10" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="November" value="11" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                        <v-col cols="auto" style="width:150px">
                          <v-checkbox :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.schedule_month" label="December" value="12" hide-details style="padding-top:0px"></v-checkbox>
                        </v-col>
                      </v-row>
                      <span class="body-1 font-weight-light white--text">Select the day to be executed.</span>
                      <v-select :readonly="information_dialog_mode == 'parameters'" filled v-model="information_dialog_data.schedule_month_day" label="Day" :items="[{id: 'first', val: 'First day of the month'}, {id: 'last', val: 'Last day of the month'}]" item-value="id" item-text="val" :rules="[v => !!v || '']" required hide-details style="margin-top:10px; margin-bottom:15px"></v-select>
                    </div>
                    <div v-show="nextExecution != null" style="margin-top:15px; margin-bottom:5px">
                      <div class="body-1 font-weight-light white--text">The execution will start at:</div>
                      <v-text-field solo readonly v-model="nextExecution" hide-details style="margin-top:10px"></v-text-field>
                    </div>
                  </div>
                  <!-- START EXECUTION -->
                  <div v-show="!schedule_enabled && information_dialog_mode != 'parameters'" style="margin-top:15px">
                    <v-tooltip right>
                      <template v-slot:activator="{ on }">
                        <span v-on="on" class="subtitle-1 font-weight-regular white--text">
                          START
                          <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                        </span>
                      </template>
                      <span>Enable this option to start the execution right away after being created.</span>
                    </v-tooltip>
                  </div>
                  <v-checkbox v-show="!schedule_enabled && information_dialog_mode != 'parameters'" :readonly="information_dialog_mode == 'parameters'" v-model="information_dialog_data.start_execution" label="Start execution" color="primary" hide-details style="margin-top:15px; margin-bottom:20px; padding:0px"></v-checkbox>
                  <v-divider v-if="information_dialog_mode != 'parameters'" style="margin-top:15px"></v-divider>
                  <div v-if="information_dialog_mode != 'parameters'" style="margin-top:20px">
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
        <v-btn text color="info" @click="schedule_now">Now</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="#EF5354" @click="schedule_close">Cancel</v-btn>
        <v-btn text color="#00b16a" @click="schedule_submit">Confirm</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="schedule_mode=='time'" v-model="schedule_time" color="info" format="24hr" scrollable>
        <v-btn text color="info" @click="schedule_now">Now</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="#EF5354" @click="schedule_close">Cancel</v-btn>
        <v-btn text color="#00b16a" @click="schedule_submit">Confirm</v-btn>
      </v-time-picker>
    </v-dialog>

    <v-dialog v-model="query_dialog" eager persistent max-width="896px">
      <v-toolbar flat dense color="primary">
        <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{ query_dialog_icon }}</v-icon>{{ query_dialog_title }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon @click="query_dialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
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
                  <div v-if="query_dialog_mode == 'info'">
                    <v-btn color="primary" @click="query_dialog=false">Close</v-btn>
                  </div>
                  <div v-else>
                    <v-btn color="#00b16a" @click="queryActionConfirm()">Confirm</v-btn>
                    <v-btn color="#EF5354" @click="query_dialog=false" style="margin-left:5px">Cancel</v-btn>
                  </div>
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
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%">
            <v-layout wrap>
              <v-flex xs12>
                <v-card>
                  <v-toolbar flat dense color="#2e3131">
                    <v-toolbar-title class="white--text subtitle-1">SELECT EXECUTION</v-toolbar-title>
                  </v-toolbar>
                  <v-divider></v-divider>
                  <v-data-table :headers="executions.headers" :items="executions.items" item-key="id" class="elevation-1" mobile-breakpoint="0">
                    <template v-slot:item="props">
                      <tr :style="`background-color:` + selectRow(props.item.id)">
                        <td>{{ props.item.environment }}</td>
                        <td><v-icon small :title="props.item.mode.charAt(0).toUpperCase() + props.item.mode.slice(1).toLowerCase()" :color="getModeColor(props.item.mode)" :style="`text-transform:capitalize; margin-left:${props.item.mode == 'BASIC' ? '8px' : '6px'}`">{{ props.item.mode == 'BASIC' ? 'fas fa-chess-knight' : 'fas fa-chess-queen' }}</v-icon></td>
                        <td><span :style="'color: ' + getMethodColor(props.item.method.toUpperCase())">{{ props.item.method.toUpperCase() }}</span></td>
                        <td>
                          <v-icon v-if="props.item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
                          <v-icon v-else-if="props.item.status == 'SCHEDULED'" :title="parseSchedule(props.item['schedule_type'], dateFormat(props.item['scheduled']))" small style="color: #ff9800; margin-left:8px;">fas fa-clock</v-icon>
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
                          <v-btn icon @click="selectExecution(props.item.uri)"><v-icon title="Select execution" small>fas fa-arrow-right</v-icon></v-btn>
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

    <v-dialog v-model="shareDeploymentDialog" max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-share</v-icon>SHARE DEPLOYMENT</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="shareDeploymentDialog = false"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px">
          <v-container>
            <v-layout wrap>
              <v-flex xs12>
                <div class="text-body-1 font-weight-regular white--text">EXECUTION</div>
                <v-text-field solo v-model="shareDeploymentUrl" readonly class="font-weight-light" style="padding-top:10px" hide-details>
                  <template v-slot:append>
                    <v-btn @click="copyClipboard(shareDeploymentUrl)" title="Copy" icon><v-icon small>fas fa-copy</v-icon></v-btn>
                  </template>
                </v-text-field>
                <div class="text-body-1 font-weight-regular white--text" style="margin-top:15px">RESULTS</div>
                <v-text-field solo v-model="shareDeploymentResultsUrl" readonly class="font-weight-light" style="padding-top:10px" hide-details>
                  <template v-slot:append>
                    <v-btn :href="shareDeploymentResultsUrl" target="_blank" title="Open" icon><v-icon small>fas fa-external-link-alt</v-icon></v-btn>
                    <v-btn @click="copyClipboard(shareDeploymentResultsUrl)" title="Copy" icon><v-icon small>fas fa-copy</v-icon></v-btn>
                  </template>
                </v-text-field>
                <v-btn @click="shareDeployment" block :color="deployment.shared ? '#EF5354' : '#00b16a'" style="margin-top:20px">{{ deployment.shared ? 'Unshare Deployment' : 'Share Deployment' }}</v-btn>
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

  // RESULTS
  import Results from './Results'

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
      validation_items: [],
      validation_error: false,

      // Execution
      execution_headers: [],
      execution_summary: [],
      execution_items: [],

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
      query_dialog_icon: '',
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
      schedule_date2: '',
      schedule_time2: '',
      schedule_datetime: '',

      // Share Deployment Dialog
      shareDeploymentDialog: false,
      shareDeploymentUrl: '',
      shareDeploymentResultsUrl: '',

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
        mode: 'text/x-mysql',
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
      loading: true,
      timer: null,

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: '',

      // Previous Route
      prevRoute: null
    }),
    beforeRouteEnter(to, from, next) {
      next(vm => {
        vm.prevRoute = from
      })
    },
    components: { codemirror, Results },
    created() {
      this.init()
    },
    computed: {
      nextExecution() {
        const now = moment().seconds(0).milliseconds(0)
        if (this.schedule_time2.length == 0) return null
        if (this.information_dialog_data.schedule_type == 'one_time') {
          const schedule = moment(this.schedule_date2 + ' ' + this.schedule_time2, "YYYY-MM-DD HH:mm")
          if (this.schedule_date2.length == 0) return null
          return schedule.format("YYYY-MM-DD HH:mm Z (dddd)")
        }
        else if (this.information_dialog_data.schedule_type == 'daily') {
          const schedule = moment(now.format("YYYY-MM-DD") + ' ' + this.schedule_time2, "YYYY-MM-DD HH:mm")
          if (schedule >= now) return schedule.format("YYYY-MM-DD HH:mm Z (dddd)")
          else return schedule.add(1, 'days').format("YYYY-MM-DD HH:mm Z (dddd)")
        }
        else if (this.information_dialog_data.schedule_type == 'weekly') {
          if (this.information_dialog_data.schedule_week.length == 0) return null
          const schedule = moment(now.format("YYYY-MM-DD") + ' ' + this.schedule_time2, "YYYY-MM-DD HH:mm")
          const startDays = this.information_dialog_data.schedule_week.map(x => moment(schedule.isoWeekday(Number(x)))).sort((a,b) => moment(a).diff(b))
          const startDay = startDays.find(x => x >= now)
          if (startDay === undefined) return startDays[0].add(1, 'weeks').format("YYYY-MM-DD HH:mm Z (dddd)")
          else return startDay.format("YYYY-MM-DD HH:mm Z (dddd)")
        }
        else if (this.information_dialog_data.schedule_type == 'monthly') {
          if (this.information_dialog_data.schedule_month.length == 0) return null
          const schedule = moment(now.format("YYYY-MM-DD") + ' ' + this.schedule_time2, "YYYY-MM-DD HH:mm")
          const startDays = this.information_dialog_data.schedule_month.map(x => {
            let date = moment(schedule.year() + '-' + ('0' + x).slice(-2) + '-01', "YYYY-MM-DD")
            if (this.information_dialog_data.schedule_month_day == 'last') date = moment(schedule.year() + '-' + ('0' + x).slice(-2) + '-' + date.endOf('month').format("DD"), "YYYY-MM-DD")
            return date
          }).sort((a,b) => moment(a).diff(b))
          const startDay = startDays.find(x => x >= now)
          if (startDay === undefined) return startDays[0].add(1, 'year').format("YYYY-MM-DD HH:mm Z (dddd)")
          else return startDay.format("YYYY-MM-DD HH:mm Z (dddd)")
        }
        return null
      }
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
        if (this.$route.params.uri === undefined) this.notification('Invalid Deployment Identifier', '#EF5354')
        else {
          this.getDeployment()
          this.getCode()
        }
      },
      goBack() {
        if (this.prevRoute == null) this.$router.push('/deployments')
        else this.$router.back()
      },
      getCode() {
        axios.get('/deployments/blueprint')
          .then((response) => {
            this.code = response.data.data
          })
          .catch((error) => {
            if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
      },
      getDeployment() {
        // Get Deployment Data
        axios.get('/deployments', { params: { uri: this.$route.params.uri } })
          .then((response) => {
            const data = response.data.deployment
            this.environments = response.data.environments
            this.parseRequest(data)
            if (this.$router.currentRoute.name == 'deployments.execution') {
              if (data['status'] == 'QUEUED' || data['status'] == 'STARTING' || data['status'] == 'STOPPING' || data['status'] == 'IN PROGRESS') {
                clearTimeout(this.timer)
                this.timer = setTimeout(this.getDeployment, 1000)
              }
              else this.start_execution = false
            }
            this.loading = false
          })
          .catch((error) => {
            this.loading = false
            if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
        this.validation_items = []
        this.execution_headers = []
        this.execution_items = []
        this.execution_summary = []
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
        this.deployment['environment'] = { id: data['environment_id'], name: data['environment_name'], shared: data['environment_shared'], secured: data['environment_secured'] }
        this.deployment['query_headers'] = [{text: 'Query', value: 'query'}]
        this.deployment['queries'] = []
        this.deployment['databases'] = this.deployment['mode'] == 'BASIC' ? data['databases'] : ''
        this.deployment['code'] = this.deployment['mode'] == 'PRO' ? data['code'] : ''
        this.deployment['method'] = data['method'].toLowerCase()
        this.getExecutions()
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
        this.deployment['shared'] = data['shared']
        this.deployment['overall'] = data['overall']
        this.deployment['owner'] = data['owner']

        // Parse Queries
        if (this.deployment['mode'] == 'BASIC') {
          let items = JSON.parse(data['queries'])
          for (let i = 0; i < items.length; ++i) this.deployment['queries'].push({id: i+1, query: items[i]['q']})
        }

        // Parse Shared
        this.shareDeploymentUrl = window.location.href
        this.shareDeploymentResultsUrl = window.location.protocol + '//' + window.location.host + `/results/` + this.deployment['uri']

        // Parse Scheduled
        this.deployment['schedule_type'] = 'one_time'
        this.deployment['schedule_value'] = ''
        this.deployment['schedule_week'] = this.deployment['schedule_month'] = []
        this.deployment['schedule_month_day'] = 'first'
        this.schedule_date = this.schedule_date2 = this.schedule_time = this.schedule_time2 = ''
        if (this.deployment['scheduled'] && this.deployment['status'] == 'SCHEDULED') {
          if (data['schedule_type'] == null) { // 'one_time'
            this.deployment['schedule_value'] = moment(data['scheduled']).format("YYYY-MM-DD HH:mm")
            this.schedule_date = moment(data['scheduled']).format("YYYY-MM-DD")
            this.schedule_date2 = this.schedule_date
            this.schedule_time = moment(data['scheduled']).format("HH:mm")
            this.schedule_time2 = this.schedule_time
          }
          else {
            this.schedule_date = moment().format("YYYY-MM-DD")
            this.schedule_time2 = moment.utc(this.schedule_date + ' ' + data['schedule_value']).local().format("HH:mm")
            this.deployment['schedule_type'] = data['schedule_type']
            this.deployment['schedule_value'] = this.schedule_time2
          }
          if (this.deployment['schedule_type'] == 'weekly') {
            this.deployment['schedule_week'] = JSON.parse(data['schedule_rules'])['rules'].map(x => x.toString())
          }
          else if (this.deployment['schedule_type'] == 'monthly') {
            this.deployment['schedule_month'] = JSON.parse(data['schedule_rules'])['rules'].map(x => x.toString())
            this.deployment['schedule_month_day'] = JSON.parse(data['schedule_rules'])['day']
          }
        }

        // Add new 'Scheduled' column if not exist
        if (this.deployment['scheduled']) {
          let found = false
          for (let h = 0; h < this.information_headers.length; ++h) {
            if (this.information_headers[h]['text'] == 'Scheduled') { found = true; break; }
          }
          if (!found) this.information_headers.splice(7, 0, { text: 'Scheduled', value: 'scheduled', sortable: false })
        }

        // Add Deployment to the information table
        this.information_items = []
        this.information_items.push(this.deployment)

        // +---------------------+
        // | PARSE PROGRESS DATA |
        // +---------------------+
        if (data['progress']) {
          this.deployment['progress'] = JSON.parse(data['progress'])
          if ('validation' in this.deployment['progress']) this.deployment['progress']['validation'].sort((a,b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()))
          if ('execution' in this.deployment['progress']) this.deployment['progress']['execution'].sort((a,b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()))

          // Parse Last Updated
          this.last_updated = this.deployment['progress']['updated']

          // Parse Validation
          this.parseValidation()

          // Parse Execution
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
        this.validation_items = [{}]

        // Fill variables
        for (const value of Object.values(this.deployment['progress']['validation'])) {
          this.validation_headers.push({ text: value.name, align: 'left', value: value.id, sortable: false, shared: value.shared})
          var status = 'VALIDATING' 
          if ('success' in value) {
            status = (value['success'] ? 'SUCCEEDED' : 'FAILED')
            if (!this.validation_error && !value['success']) this.validation_error = true
          }
          this.validation_items[0][value.id] = status
        }
      },
      parseExecution() {
        // Init variables
        var execution_headers = []
        var execution_summary = [{}]
        var execution_items = []
        var overall_progress = {}

        // Init Execution Headers (if hasn't started yet)
        if (!('execution' in this.deployment['progress'])) {
          if (this.deployment['method'] != 'validate' && this.validation_items.length > 0) {
            let succeeded = true
            for (let value of Object.values(this.validation_items[0])) { 
              succeeded &= (value == 'SUCCEEDED')
            }
            if (succeeded) {
              this.execution_headers = JSON.parse(JSON.stringify(this.validation_headers))
              for (let region of this.execution_headers) {
                execution_summary[0][region.id] = "Initiating..."
              }
            }
            this.execution_summary = JSON.parse(JSON.stringify(execution_summary))
          }
          return
        }

        // Init Execution Progress (if has started)
        for (const region of Object.values(this.deployment['progress']['execution'])) {
          overall_progress[region.id] = {"d": 0, "t": 0}
          execution_headers.push({ text: region.name, align: 'left', value: region.id, sortable: false, shared: region.shared})
          for (const [index, server] of Object.entries(region.servers.sort((a,b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase())))) {
            overall_progress[region.id]['d'] += server['d']
            overall_progress[region.id]['t'] += server['t']
            let progress = server['p'] + '% (' + server['d'] + '/' + server['t'] + ' DBs)'
            if (index >= execution_items.length) execution_items.push({[region.id]: {"server": server.name, "shared": server.shared, "progress": progress}})
            else execution_items[index][region.id] = {"server": server.name, "shared": server.shared, "progress": progress}
          }
  
          // Add overall
          if (region.servers.length == 0) {
            if ('logs' in this.deployment['progress']) execution_summary[0][region.id] = "100% (0/0 DBs)"
            else execution_summary[0][region.id] = "Initiating..."
          }
          else {
            var execution_total = (overall_progress[region.id]['d'] / overall_progress[region.id]['t'] * 100).toFixed(2)
            if (execution_total == 100) execution_total = 100
            execution_summary[0][region.id] = execution_total + '% (' + overall_progress[region.id]['d'] + '/' + overall_progress[region.id]['t'] + ' DBs)'
          }
        }

        // Assign variables
        this.execution_headers = JSON.parse(JSON.stringify(execution_headers))
        this.execution_summary = JSON.parse(JSON.stringify(execution_summary))
        this.execution_items = JSON.parse(JSON.stringify(execution_items))
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
      parseSchedule(type, value) {
        if (type == null) return 'Scheduled (One time): ' + value.slice(0,-3)
        return 'Scheduled (' + type.replace('_',' ').charAt(0).toUpperCase() + type.replace('_',' ').slice(1) + '): ' + value.slice(0,-3)
      },
      showResults() {
        // Show Results View
        this.show_results = true
      },
      getExecutions() {
        // Get Deployment Executions
        axios.get('/deployments/executions', { params: { uri: this.$route.params.uri } })
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
            if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
      },
      // ------------------
      // NAVIGATION METHODS
      // ------------------
      parameters() {
        this.information_dialog_mode = 'parameters'
        this.information_dialog_execution_mode = this.deployment['mode']
        this.information_dialog_query_selected = []
        this.cmOptions.readOnly = true
        this.information_dialog_data = JSON.parse(JSON.stringify(this.deployment))
        this.schedule_enabled = this.deployment['scheduled'] !== null
        this.schedule_datetime = this.deployment['schedule_value']
        this.information_dialog = true
      },
      edit() {
        this.information_dialog_mode = (this.deployment['status'] == 'CREATED' || this.deployment['status'] == 'SCHEDULED') ? 'edit' : 're-deploy'
        if (this.information_dialog_mode == 're-deploy') {
          this.schedule_enabled = false
          this.schedule_mode = 'date'
          this.schedule_date = ''
          this.schedule_time = ''
          this.schedule_datetime = ''
        }
        else this.schedule_enabled = this.deployment['scheduled'] !== null
        this.schedule_datetime = this.deployment['schedule_value']
        this.information_dialog_execution_mode = this.deployment['mode']
        this.information_dialog_query_selected = []
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
        this.action_dialog_text = ''
        this.stop_execution_mode = (this.deployment['stopped'] == 'graceful') ? 'forceful' : 'graceful' 
        this.action_dialog = true
      },
      actionSubmit() {
        if (this.action_dialog_mode == 'start') this.actionSubmitStart()
        else if (this.action_dialog_mode == 'stop') this.actionSubmitStop()
      },
      actionSubmitStart() {
        this.action_dialog = false
        // Build parameters
        const payload = {
          uri: this.$route.params.uri,
          url: window.location.protocol + '//' + window.location.host
        }
        axios.post('/deployments/start', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.start_execution = true
          this.getDeployment()
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
            uri: this.$route.params.uri,
            mode: this.stop_execution_mode
          }
          axios.post('/deployments/stop', payload)
          .catch((error) => {
            if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
      },
      schedule_now() {
        const date = moment()
        if (this.schedule_mode == 'date') this.schedule_date = date.format("YYYY-MM-DD")
        else if (this.schedule_mode == 'time') this.schedule_time = date.format("HH:mm")
      },
      schedule_change() {
        if (this.information_dialog_mode == 'parameters') return
        const date = moment()
        if (this.schedule_datetime.length == 0) {
          this.schedule_date = date.format("YYYY-MM-DD")
          this.schedule_time = date.format("HH:mm")
        }
        else if (this.information_dialog_data['schedule_type'] == 'one_time') {
          this.schedule_date = moment(this.schedule_datetime, "YYYY-MM-DD HH:mm:ss").format('YYYY-MM-DD')
          this.schedule_date2 = this.schedule_date
          this.schedule_time = moment(this.schedule_datetime, "YYYY-MM-DD HH:mm:ss").format('HH:mm')
          this.schedule_time2 = this.schedule_time
        }
        else {
          this.schedule_time = this.schedule_datetime
          this.schedule_time2 = this.schedule_time
        }
        this.schedule_mode = (this.information_dialog_data.schedule_type == 'one_time') ? 'date' : 'time'
        this.scheduleDialog = true
      },
      schedule_submit() {
        if (this.schedule_mode == 'date') {
          this.schedule_mode = 'time'
        }
        else if (this.schedule_mode == 'time') {
          this.schedule_time2 = this.schedule_time
          if (this.information_dialog_data.schedule_type == 'one_time') {
            this.schedule_date2 = this.schedule_date
            this.schedule_datetime = this.schedule_date + ' ' + this.schedule_time
          }
          else this.schedule_datetime = this.schedule_time
          this.scheduleDialog = false
        }
      },
      // ------------------------
      // SELECT EXECUTION DIALOG
      // ------------------------
      selectExecution(uri) {
        this.select_dialog = false
        if (this.deployment['uri'] != uri) {
          this.$router.push({ name: 'deployments.execution', params: { uri: uri }})
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
        // Check environment
        if (this.information_dialog_data.environment != null) {
          const environment_found = this.environments.find(x => x.id == this.information_dialog_data.environment.id) !== undefined
          if (!environment_found) this.information_dialog_data.environment = null
        }
        // Validate form
        if (!this.$refs.form.validate() || this.information_dialog_data.environment == null) {
          this.notification('Please fill the required fields', '#EF5354')
          return
        }
        if (this.information_dialog_execution_mode == 'BASIC' && this.information_dialog_data.queries.length == 0) {
          this.notification('Please enter a query to deploy', '#EF5354')
          return
        }
        if (this.schedule_enabled && this.schedule_datetime.length == 0) {
          this.notification('Please enter a schedule time', '#EF5354')
          return
        }
        if (this.schedule_enabled && this.information_dialog_data.schedule_type == 'weekly' && this.information_dialog_data.schedule_week.length == 0) {
          this.notification('Please select at least one day of week', '#EF5354')
          return
        }
        if (this.schedule_enabled && this.information_dialog_data.schedule_type == 'monthly' && this.information_dialog_data.schedule_month.length == 0) {
          this.notification('Please select at least one month', '#EF5354')
          return
        }
        // Hide Results View
        this.show_results = false
        // Build parameters
        var payload = {
          uri: this.$route.params.uri,
          mode: this.information_dialog_execution_mode,
          environment: this.information_dialog_data.environment.id,
          method: this.information_dialog_data.method.toUpperCase(),
          url: window.location.protocol + '//' + window.location.host
        }
        // Build different modes
        if (this.information_dialog_execution_mode == 'BASIC') {
          payload['databases'] = this.information_dialog_data.databases
          payload['queries'] = this.information_dialog_data.queries.map(x => x.query)
        }
        else if (this.information_dialog_execution_mode == 'PRO') {
          payload['code'] = this.information_dialog_data.code
        }
        // Build scheduled & start_execution
        if (this.schedule_enabled) {
          payload['schedule_type'] = this.information_dialog_data.schedule_type
          if (this.information_dialog_data.schedule_type == 'one_time') {
            payload['schedule_value'] = moment(this.schedule_datetime).utc().format("YYYY-MM-DD HH:mm")
          }
          else if (this.information_dialog_data.schedule_type == 'daily') {
            payload['schedule_value'] = moment(this.schedule_datetime, "HH:mm").utc().format("HH:mm")
          }
          else if (this.information_dialog_data.schedule_type == 'weekly') {
            payload['schedule_value'] = moment(this.schedule_datetime, "HH:mm").utc().format("HH:mm")
            payload['schedule_rules'] = {"rules": this.information_dialog_data.schedule_week.map(Number).sort((a, b) => a - b)}
          }
          else if (this.information_dialog_data.schedule_type == 'monthly') {
            payload['schedule_value'] = moment(this.schedule_datetime, "HH:mm").utc().format("HH:mm")
            payload['schedule_rules'] = {"rules": this.information_dialog_data.schedule_month.map(Number).sort((a, b) => a - b), "day": this.information_dialog_data.schedule_month_day}
          }
        }
        else payload['start_execution'] = this.information_dialog_data.start_execution === undefined ? false : this.information_dialog_data.start_execution
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
          if (this.information_dialog_mode == 're-deploy') {
            this.$router.push({ name: 'deployments.execution', params: { uri: data['uri'] }})
          }
          else this.getDeployment()
          // Hide the Information dialog
          this.information_dialog = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
        this.query_dialog_icon = 'fas fa-plus'
        this.cmOptions2.readOnly = false
        this.query_dialog = true
      },
      showQuery() {
        this.query_dialog_mode = 'info'
        this.query_dialog_code = this.information_dialog_query_selected.map(x => x.query).join('\n\n')
        this.query_dialog_title = 'DETAILS'
        this.query_dialog_icon = 'fas fa-bookmark'
        this.cmOptions2.readOnly = true
        this.query_dialog = true
      },
      editQuery () {
        this.query_dialog_mode = 'edit'
        this.query_dialog_code = this.information_dialog_query_selected[0]['query']
        this.query_dialog_title = 'EDIT QUERY'
        this.query_dialog_icon = 'fas fa-feather-alt'
        this.cmOptions2.readOnly = false
        this.query_dialog = true
      },
      deleteQuery() {
        this.query_dialog_mode = 'delete'
        this.query_dialog_title = 'DELETE QUERY'
        this.query_dialog_icon = 'fas fa-minus'
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
        this.notification('Queries added', '#00b16a')
      },
      editQueryConfirm() {
        // Parse Queries
        if (this.query_dialog_code.trim().length == 0) {
          this.notification('Please enter a query', '#EF5354')
          return
        }
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
        this.notification('Query edited', '#00b16a')
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
        this.notification('Selected queries removed', '#00b16a')
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
        if (start < i && this.query_dialog_code.substring(start, i).trim().length != 0) queries.push({"id": id, "query": this.query_dialog_code.substring(start, i).trim()})
        // Return parsed queries
        return queries
      },
      // -------------------------------------
      // SHARE DEPLOYMENT
      // -------------------------------------
      copyClipboard(text) {
        navigator.clipboard.writeText(text)
        this.notification('Link copied to clipboard', '#00b16a', Number(2000))
      },
      shareDeployment() {
        // Build parameters
        const payload = {
          uri: this.$route.params.uri,
          shared: !this.deployment['shared']
        }
        axios.post('/deployments/shared', payload)
        .then((response) => {
          // Update new shared value
          this.deployment['shared'] = !this.deployment['shared']
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
      regionColor (region) {
        if (region === undefined) return 'background-color: rgb(250, 130, 49);'
        if (region.startsWith('100%')) return 'background-color: rgb(0, 177, 106);'
        return 'background-color: rgb(250, 130, 49);'
      },
      regionIcon (progress) {
        if (progress === undefined) return 'fas fa-spinner'  
        if (progress.startsWith('100%')) return 'fas fa-check'
        return 'fas fa-spinner'  
      },
      serverColor (progress) {
        if (progress.startsWith('100%')) return 'color: #00b16a;'
        else return 'color: rgb(250, 130, 49);'
      },
      dateFormat(date) {
        if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
        return date
      },
      notification(message, color, time=Number(3000)) {
        this.snackbarText = message
        this.snackbarColor = color
        this.snackbarTimeout = time
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
      'information_dialog_data.schedule_type'(val) {
        if (val == 'one_time') this.schedule_datetime = (this.schedule_date2.length == 0) ? '' : (this.schedule_date2 + ' ' + this.schedule_time2).trim()
        else this.schedule_datetime = this.schedule_time2
      },
      query_dialog (val) {
        if (!val) return
        this.$nextTick(() => {
          if (this.$refs.codemirror === undefined) return
          const codemirror = this.$refs.codemirror.codemirror
          setTimeout(() => { codemirror.refresh(); codemirror.focus() }, 200)
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