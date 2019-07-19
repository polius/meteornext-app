<template>
  <div>
    <v-toolbar dark color="primary">
      <v-toolbar-title class="white--text">INFO</v-toolbar-title>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-toolbar-title class="white--text">Release 3.33.0</v-toolbar-title>
      <v-btn :disabled="stopExecution" flat style="margin-left:30px;" @click="stop()"><v-icon style="padding-right:10px">fas fa-stop-circle</v-icon>STOP EXECUTION</v-btn>
      <v-progress-circular v-show="stopExecution" :size="25" indeterminate color="white"></v-progress-circular>
      <v-toolbar-title v-show="stopExecution" class="subheading white--text">Stopping the execution...</v-toolbar-title>
      <v-spacer></v-spacer>
      <router-link class="nav-link" to="/deployments"><v-btn icon><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn></router-link>
    </v-toolbar>

    <v-progress-linear :indeterminate="false" height="5" color="info" style="margin:0px;" value="100"></v-progress-linear>

    <v-card>
      <v-card-text>
        <!-- <p>DeploymentID {{ deploymentID }}</p> -->

        <!-- INFORMATION -->
        <div class="title font-weight-regular" style="padding-bottom:10px;">STATUS</div>
        <v-chip label color="success" style="margin-left:0px;">Execution Finished Successfully</v-chip>
        <a href="https://dba.inbenta.me/meteor/?uri=24a5bd97-4fae-4868-b960-2b30b3b184f4" target="_blank"><v-chip label color="primary">https://dba.inbenta.me/meteor/?uri=24a5bd97-4fae-4868-b960-2b30b3b184f4</v-chip></a>

        <v-card style="margin-top:10px;">
          <v-data-table :headers="metadata_headers" :items="metadata_data" hide-actions>
            <template v-slot:items="props">
              <td>{{ props.item.name }}</td>
              <td>{{ props.item.environment }}</td>
              <td class="text-xs-center"><v-chip label :color="getModeColor(props.item.mode)" dark>{{ props.item.mode }}</v-chip></td>
              <td class="text-xs-center"><v-chip label :color="getStatusColor(props.item.status)" dark>{{ props.item.status }}</v-chip></td>
              <td>{{ props.item.started }}</td>
              <td>{{ props.item.ended }}</td>
              <td>{{ props.item.time }}</td>
            </template>
          </v-data-table>
        </v-card>

        <!-- PROCESS -->
        <div class="title font-weight-regular" style="padding-top:20px; padding-left:1px;">PROCESS</div>
        <v-layout row wrap style="margin-top:20px;">
          <v-flex xs3 style="padding-right:10px;">
            <!-- validation -->
            <v-card dark>
              <v-data-table :headers="validation_headers" :items="validation_data" hide-actions>
                <template v-slot:items="props">
                  <td>{{ props.item.status }}</td>
                </template>
              </v-data-table>
            </v-card>
          </v-flex>

          <!-- deployment -->
          <v-flex xs3 style="padding-right:10px;">
            <v-card dark>
              <v-data-table :headers="deployment_headers" :items="deployment_data" hide-actions>
                <template v-slot:items="props">
                  <td>{{ props.item.status }}</td>
                </template>
              </v-data-table>
            </v-card>
          </v-flex>

          <!-- logs -->
          <v-flex xs3 style="padding-right:10px;">
            <v-card dark>
              <v-data-table :headers="logs_headers" :items="logs_data" hide-actions>
                <template v-slot:items="props">
                  <td>{{ props.item.status }}</td>
                </template>
              </v-data-table>
            </v-card>
          </v-flex>

          <!-- post-execution -->
          <v-flex xs3>
            <v-card dark>
              <v-data-table :headers="post_headers" :items="post_data" hide-actions>
                <template v-slot:items="props">
                  <td>{{ props.item.status }}</td>
                </template>
              </v-data-table>
            </v-card>
          </v-flex>
        </v-layout>

        <!-- QUERIES -->
        <div class="title font-weight-regular" style="padding-top:20px; padding-left:1px; padding-bottom:10px;">QUERIES</div>

        <v-layout style="margin-top:10px; margin-bottom:10px;">
          <v-flex xs6 style="padding-right:10px;">
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
      metadata_headers: [
        { text: 'Name', align: 'left', value: 'name', sortable: false },
        { text: 'Environment', value: 'environment', sortable: false },
        { text: 'Mode', align: 'center', value: 'mode', sortable: false },
        { text: 'Status', align:'center', value: 'status', sortable: false },
        { text: 'Started', align: 'left', value: 'started', sortable: false },
        { text: 'Ended', align: 'left', value: 'ended', sortable: false },
        { text: 'Overall Time', value: 'time', sortable: false }
      ],
      metadata_data: [
        {
          id: 1,
          name: 'Release 3.33.0',
          environment: 'Production',
          mode: 'DEPLOYMENT',
          status: 'SUCCESS',
          started: '2019-07-07 08:00:00',
          ended: '2019-07-07 08:12:15',
          time: '12m 15s'
        }
      ],
      validation_headers: [
        { text: 'VALIDATION', align:'left', value: 'status', sortable: false }
      ],
      validation_data: [
        { status: "[LOCAL] Region 'AWS-EU' Started..." },
        { status: "[SSH] Region 'AWS-US' Started..." },
        { status: "[SSH] Region 'AWS-BR' Started..." },
        { status: "[SSH] Region 'AWS-JP' Started..." },
        { status: "[SSH] Region 'AWS-BR' Finished." },
        { status: "[SSH] Region 'AWS-JP' Finished." },
        { status: "[SSH] Region 'AWS-US' Finished." },
        { status: "[LOCAL] Region 'AWS-EU' Finished." }
      ],
      deployment_headers: [
        { text: 'DEPLOYMENT', align:'left', value: 'status', sortable: false }
      ],
      deployment_data: [
        { status: "[LOCAL] Region 'AWS-EU' Started..." },
        { status: "[SSH] Region 'AWS-US' Started..." },
        { status: "[SSH] Region 'AWS-BR' Started..." },
        { status: "[SSH] Region 'AWS-JP' Started..." },
        { status: "[SSH] Region 'AWS-BR' Finished." },
        { status: "[SSH] Region 'AWS-JP' Finished." },
        { status: "[SSH] Region 'AWS-US' Finished." },
        { status: "[LOCAL] Region 'AWS-EU' Finished." }
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
        { text: 'POST EXECUTION', align:'left', value: 'status', sortable: false }
      ],
      post_data: [
        { status: "Uploading Logs to Amazon S3 Bucket 'meteor'..." },
        { status: "Cleaning Remote Environments..." },
        { status: "Cleaning Local Environments..." },
        { status: "Cleaning Remaining Processes..." },
        { status: "Sending Slack Message to #meteor..." }
      ],
      summary_headers: [
        { text: 'Total Queries', align:'left', value: 'total', sortable: false },
        { text: 'Queries Succeeded', align:'left', value: 'succeeded', sortable: false },
        { text: 'Queries Failed', align:'left', value: 'failed', sortable: false }
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