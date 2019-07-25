<template>
  <div>
    <v-toolbar dark color="primary">
      <v-toolbar-title class="white--text">INFO</v-toolbar-title>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-toolbar-title class="white--text">Release 3.35.0</v-toolbar-title>
      <!-- <v-btn :disabled="stopExecution" flat style="margin-left:30px;" @click="stop()"><v-icon style="padding-right:10px">fas fa-stop-circle</v-icon>STOP EXECUTION</v-btn>
      <v-progress-circular v-show="stopExecution" :size="25" indeterminate color="white"></v-progress-circular> -->
      <v-chip label color="success" style="margin-left:30px;">Execution Finished Successfully</v-chip>
      <v-spacer></v-spacer>
      <div class="subheading font-weight-regular" style="padding-right:20px;">Updated on <b>2019-07-25 12:10:08</b></div>
      <router-link class="nav-link" to="/deployments"><v-btn icon><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn></router-link>
    </v-toolbar>

    <v-progress-linear :indeterminate="false" height="5" color="info" style="margin:0px;" value="100"></v-progress-linear>

    <v-card>
      <v-card-text>
        <!-- <p>DeploymentID {{ deploymentID }}</p> -->

        <!-- STATUS -->
        <v-card>
          <v-data-table :headers="status_headers" :items="status_data" hide-actions>
            <template v-slot:items="props">
              <td>{{ props.item.name }}</td>
              <td>{{ props.item.environment }}</td>
              <td class="error--text"><b>{{ props.item.mode }}</b></td>
              <td>{{ props.item.started }}</td>
              <td>{{ props.item.ended }}</td>
              <td>{{ props.item.time }}</td>
              <td>
                <a :href="props.item.logs" target="_blank">
                  <v-btn icon @click="logs(props.item)" style="margin-left:-5px;"><v-icon small>fas fa-meteor</v-icon></v-btn>
                </a>
              </td>
            </template>
          </v-data-table>
        </v-card>

        <!-- VALIDATION -->
        <div class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">VALIDATION</div>
        <!-- validation -->
        <v-card dark style="margin-top:15px;">
          <v-data-table :headers="validation_headers" :items="validation_data" hide-actions>
            <template v-slot:items="props">
              <td class="success--text"><b>{{ props.item.r1 }}</b></td>
              <td class="warning--text"><b>{{ props.item.r2 }}</b></td>
              <td class="warning--text"><b>{{ props.item.r3 }}</b></td>
              <td class="error--text"><b>{{ props.item.r4 }}</b></td>
            </template>
          </v-data-table>
        </v-card>

        <!-- EXECUTION -->
        <div class="title font-weight-regular" style="padding-top:15px; padding-left:1px;">EXECUTION</div>
        <v-card dark style="margin-top:15px;">
          <v-data-table :headers="execution_headers" :items="execution_data" hide-actions>
            <template v-slot:items="props">
              <td v-if="props.index == 0" style="padding-left:20px;"><v-chip label color="warning" dark><b>{{ props.item.r1 }}</b></v-chip></td>
              <td v-if="props.index == 0" style="padding-left:20px;"><v-chip label color="warning" dark><b>{{ props.item.r2 }}</b></v-chip></td>
              <td v-if="props.index == 0" style="padding-left:20px;"><v-chip label color="warning" dark><b>{{ props.item.r3 }}</b></v-chip></td>
              <td v-if="props.index == 0" style="padding-left:20px;"><v-chip label color="success" dark><b>{{ props.item.r4 }}</b></v-chip></td>

              <td v-if="props.index != 0" class="warning--text" style="padding-left:20px;">{{ props.item.r1 }}</td>
              <td v-if="props.index != 0" class="warning--text" style="padding-left:20px;">{{ props.item.r2 }}</td>
              <td v-if="props.index != 0" class="warning--text" style="padding-left:20px;">{{ props.item.r3 }}</td>
              <td v-if="props.index != 0" class="success--text" style="padding-left:20px;">{{ props.item.r4 }}</td>
            </template>
          </v-data-table>
        </v-card>

        <!-- After Execution Headers -->
        <v-layout row wrap style="margin-top:15px;">
          <v-flex xs6>
            <div class="title font-weight-regular" style="padding-top:20px; padding-left:1px;">POST EXECUTION</div>
          </v-flex>
          <v-flex xs6>
            <div class="title font-weight-regular" style="padding-top:20px; padding-left:7px;">QUERIES</div>
          </v-flex>
        </v-layout>

        <!-- POST EXECUTION -->
        <v-layout row wrap style="margin-top:15px;">
          <!-- logs -->
          <v-flex xs3 style="padding-right:5px;">
            <v-card dark>
              <v-data-table :headers="logs_headers" :items="logs_data" hide-actions>
                <template v-slot:items="props">
                  <td>{{ props.item.status }}</td>
                </template>
              </v-data-table>
            </v-card>
          </v-flex>
          <!-- remaining-tasks -->
          <v-flex xs3 style="padding-left:5px; padding-right:5px;">
            <v-card dark>
              <v-data-table :headers="post_headers" :items="post_data" hide-actions>
                <template v-slot:items="props">
                  <td>{{ props.item.status }}</td>
                </template>
              </v-data-table>
            </v-card>
          </v-flex>
          <!-- queries -->
          <v-flex xs6 style="padding-left:5px;">
            <v-card dark>
              <v-data-table :headers="summary_headers" :items="summary_data" hide-actions>
                <template v-slot:items="props">
                  <td>{{ props.item.total }}</td>
                  <td>{{ props.item.succeeded }}</td>
                  <td>{{ props.item.failed }}</td>
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

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" flat @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
  export default  {
    data: () => ({
      stopExecution: false,
      status_headers: [
        { text: 'Name', align: 'left', value: 'name', sortable: false },
        { text: 'Environment', value: 'environment', sortable: false },
        { text: 'Mode', align: 'left', value: 'mode', sortable: false },
        { text: 'Started', align: 'left', value: 'started', sortable: false },
        { text: 'Ended', align: 'left', value: 'ended', sortable: false },
        { text: 'Overall Time', value: 'time', sortable: false },
        { text: 'Logs', value: 'logs', sortable: false }
      ],
      status_data: [
        {
          id: 1,
          name: 'Release 3.33.0',
          environment: 'Production',
          mode: 'DEPLOYMENT',
          started: '2019-07-07 08:00:00',
          ended: '2019-07-07 08:12:15',
          time: '12m 15s',
          logs: 'https://dba.inbenta.me/meteor/?uri=24a5bd97-4fae-4868-b960-2b30b3b184f4'
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
          r1: "Succeeded",
          r2: "Validating",
          r3: "Validating",
          r4: "Failed"
        }
      ],
      execution_headers: [
        { text: 'AWS-EU', align:'left', value: 'r1', sortable: false },
        { text: 'AWS-US', align:'left', value: 'r2', sortable: false },
        { text: 'AWS-BR', align:'left', value: 'r3', sortable: false },
        { text: 'AWS-JP', align:'left', value: 'r4', sortable: false }
      ],
      execution_data: [
        { r1: "0% (0/120 DBs)", r2: "56% (756/1362 DBs)", r3: "82% (1467/1739 DBs)", r4: "100% (253/253 DBs)" },
        { r1: "awseu-sql01. 100% (21/21 DBs)", r2: "aws-sql01. 52% (12/21 DBs)", r3: "awsbr-sql01. 52% (12/21 DBs)", r4: "awsjp-sql01. 100% (153/153 DBs)" },
        { r1: "awseu-sql02. 100% (122/122 DBs)", r2: "aws-sql02. 43% (108/211 DBs)", r3: "awsbr-sql02. 8% (2/12 DBs)", r4: "awsjp-sql02. 100% (100/100 DBs)" }
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
    props: ['deploymentID'],
    methods: {
      getModeColor (mode) {
        if (mode == 'DEPLOYMENT') return 'red'
        else if (mode == 'TEST') return 'orange'
        else if (mode == 'VALIDATION') return 'green'
      },
      getStatusColor (status) {
        if (status == 'FAILED') return 'red'
        else if (status == 'WARNINGS') return 'orange'
        else if (status == 'SUCCESS') return 'green'
      },
      stop() {
        this.notification('Stopping the execution. Please wait...', 'primary')
        this.stopExecution = true
      },
      notification(message, color) {
        this.snackbarText = message
        this.snackbarColor = color 
        this.snackbar = true
      }
    }
  }
</script>